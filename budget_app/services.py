from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
from typing import Iterable, Iterator

from budget_app.errors import NotFoundError, ValidationError
from budget_app.models import Budget, SearchCriteria, Transaction
from budget_app.repositories import BudgetRepository, CategoryRepository, TransactionRepository
from budget_app.sorting import iter_latest, top_latest
from budget_app.validators import (
    parse_tags,
    validate_amount,
    validate_date,
    validate_month,
    validate_type,
)


class CategoryService:
    def __init__(
        self,
        categories: CategoryRepository,
        transactions: TransactionRepository,
    ) -> None:
        self.categories = categories
        self.transactions = transactions

    def list_categories(self) -> list[str]:
        return self.categories.list_all()

    def add_category(self, name: str) -> None:
        name = name.strip()
        if not name:
            raise ValidationError("카테고리명은 비어 있을 수 없습니다.")
        categories = self.categories.list_all()
        if name in categories:
            raise ValidationError("이미 존재하는 카테고리입니다.", name)
        categories.append(name)
        self.categories.write_categories(categories)

    def remove_category(self, name: str) -> None:
        categories = self.categories.list_all()
        if name not in categories:
            raise NotFoundError("존재하지 않는 카테고리입니다.", name)
        # 이미 거래에서 쓰는 카테고리를 삭제하면 데이터 일관성이 깨진다.
        for transaction in self.transactions.iter_all():
            if transaction.category == name:
                raise ValidationError(
                    "사용 중인 카테고리는 삭제할 수 없습니다.",
                    "먼저 해당 거래를 수정하거나 삭제하세요.",
                )
        self.categories.write_categories([category for category in categories if category != name])

    def ensure_exists(self, name: str) -> None:
        if name not in self.categories.list_all():
            raise ValidationError(
                "등록되지 않은 카테고리입니다.",
                "category add로 먼저 카테고리를 추가하세요.",
            )


class BudgetService:
    def __init__(self, budgets: BudgetRepository) -> None:
        self.budgets = budgets

    def set_budget(self, month: str, amount: str | int) -> Budget:
        budget = Budget(month=validate_month(month), amount=validate_amount(amount))
        self.budgets.upsert(budget)
        return budget

    def list_budgets(self) -> list[Budget]:
        return self.budgets.list_all()

    def show_budget(self, month: str) -> Budget | None:
        return self.budgets.find_by_month(validate_month(month))


class TransactionService:
    def __init__(
        self,
        transactions: TransactionRepository,
        categories: CategoryService,
        budgets: BudgetRepository,
    ) -> None:
        self.transactions = transactions
        self.categories = categories
        self.budgets = budgets

    def add_transaction(
        self,
        date: str,
        type_: str,
        category: str,
        amount: str | int,
        memo: str = "",
        tags: str | None = None,
    ) -> Transaction:
        # 입력값 검증과 id 생성은 저장 전에 끝내서 잘못된 데이터가 파일에 남지 않게 한다.
        transaction = Transaction(
            id=self.next_id(),
            date=validate_date(date),
            type=validate_type(type_),
            category=category,
            amount=validate_amount(amount),
            memo=memo.strip(),
            tags=parse_tags(tags),
        )
        self.categories.ensure_exists(transaction.category)
        self.transactions.append(transaction)
        return transaction

    def list_transactions(self, limit: int) -> Iterable[Transaction]:
        if limit <= 0:
            raise ValidationError("--limit은 1 이상이어야 합니다.")
        # 전체 파일을 리스트로 만들지 않고 최신 N개만 유지한다.
        return top_latest(self.transactions.iter_all(), limit)

    def search(self, criteria: SearchCriteria) -> Iterator[Transaction]:
        self._validate_criteria(criteria)
        # 조건 검사는 파일을 한 줄씩 읽는 동안 수행한다.
        matches = (
            transaction
            for transaction in self.transactions.iter_all()
            if self._matches(transaction, criteria)
        )
        return iter_latest(matches)

    def update_transaction(self, transaction_id: str, updates: dict[str, str | None]) -> Transaction:
        if all(value is None for value in updates.values()):
            raise ValidationError(
                "수정할 필드가 없습니다.",
                "--date, --type, --category, --amount, --memo, --tags 중 하나 이상 입력하세요.",
            )

        updated: Transaction | None = None

        def iter_updated() -> Iterator[Transaction]:
            # rewrite가 이 제너레이터를 소비하면서 새 파일을 만든다.
            nonlocal updated
            for transaction in self.transactions.iter_all():
                if transaction.id == transaction_id:
                    updated = self._apply_updates(transaction, updates)
                    yield updated
                else:
                    yield transaction

        self.transactions.rewrite(iter_updated())
        if updated is None:
            raise NotFoundError("해당 id의 거래가 없습니다.", transaction_id)

        return updated

    def delete_transaction(self, transaction_id: str) -> None:
        found = False

        def iter_remaining() -> Iterator[Transaction]:
            # 삭제 대상만 건너뛰고 나머지는 그대로 새 파일에 흘려보낸다.
            nonlocal found
            for transaction in self.transactions.iter_all():
                if transaction.id == transaction_id:
                    found = True
                else:
                    yield transaction

        self.transactions.rewrite(iter_remaining())
        if not found:
            raise NotFoundError("해당 id의 거래가 없습니다.", transaction_id)

    def summarize(self, month: str, top: int) -> dict[str, object]:
        month = validate_month(month)
        if top <= 0:
            raise ValidationError("--top은 1 이상이어야 합니다.")

        total_income = 0
        total_expense = 0
        category_totals: dict[str, int] = {}
        count = 0

        criteria = SearchCriteria(month=month)
        # summary는 정렬이 필요 없으므로 스트리밍으로 누적 합계만 계산한다.
        for transaction in self.transactions.iter_all():
            if not self._matches(transaction, criteria):
                continue
            count += 1
            if transaction.type == "income":
                total_income += transaction.amount
            else:
                total_expense += transaction.amount
                category_totals[transaction.category] = (
                    category_totals.get(transaction.category, 0) + transaction.amount
                )

        top_categories = sorted(category_totals.items(), key=lambda item: item[1], reverse=True)[:top]
        budget = self.budgets.find_by_month(month)
        usage_rate = None
        is_over_budget = False
        if budget:
            usage_rate = (total_expense / budget.amount) * 100
            is_over_budget = total_expense > budget.amount

        return {
            "month": month,
            "count": count,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "top_categories": top_categories,
            "budget": budget,
            "usage_rate": usage_rate,
            "is_over_budget": is_over_budget,
        }

    def export_csv(self, output_path: str, criteria: SearchCriteria) -> int:
        if not criteria.month and not (criteria.date_from or criteria.date_to):
            raise ValidationError(
                "export는 기간 조건이 필요합니다.",
                "--month 또는 --from/--to를 입력하세요.",
            )

        self._validate_criteria(criteria)
        rows = (
            transaction
            for transaction in self.transactions.iter_all()
            if self._matches(transaction, criteria)
        )
        path = Path(output_path)
        count = 0
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=["date", "type", "category", "amount", "memo", "tags"],
            )
            writer.writeheader()
            # export 결과도 최신순이어야 하므로 chunk 정렬 제너레이터를 거친다.
            for transaction in iter_latest(rows):
                writer.writerow(
                    {
                        "date": transaction.date,
                        "type": transaction.type,
                        "category": transaction.category,
                        "amount": transaction.amount,
                        "memo": transaction.memo,
                        "tags": ",".join(transaction.tags or []),
                    }
                )
                count += 1
        return count

    def import_csv(self, input_path: str) -> tuple[int, int]:
        imported = 0
        skipped = 0
        with Path(input_path).open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            required = {"date", "type", "category", "amount"}
            if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
                raise ValidationError(
                    "CSV 필수 컬럼이 부족합니다.",
                    "date,type,category,amount 헤더가 필요합니다.",
                )
            for row in reader:
                try:
                    self.add_transaction(
                        date=row["date"],
                        type_=row["type"],
                        category=row["category"],
                        amount=row["amount"],
                        memo=row.get("memo", ""),
                        tags=row.get("tags", ""),
                    )
                    imported += 1
                except ValidationError:
                    # 잘못된 행 하나 때문에 전체 import가 멈추지 않게 건너뛴다.
                    skipped += 1
        return imported, skipped

    def next_id(self) -> str:
        last_number = 0
        # 기존 id 중 가장 큰 번호를 찾아 다음 id를 만든다.
        for transaction in self.transactions.iter_all():
            if transaction.id.startswith("TX-"):
                try:
                    last_number = max(last_number, int(transaction.id.replace("TX-", "")))
                except ValueError:
                    continue
        return f"TX-{last_number + 1:06d}"

    def _apply_updates(self, transaction: Transaction, updates: dict[str, str | None]) -> Transaction:
        data: dict[str, object] = {}
        if updates.get("date"):
            data["date"] = validate_date(str(updates["date"]))
        if updates.get("type"):
            data["type"] = validate_type(str(updates["type"]))
        if updates.get("category"):
            category = str(updates["category"])
            self.categories.ensure_exists(category)
            data["category"] = category
        if updates.get("amount"):
            data["amount"] = validate_amount(str(updates["amount"]))
        if updates.get("memo") is not None:
            data["memo"] = str(updates["memo"])
        if updates.get("tags") is not None:
            data["tags"] = parse_tags(updates["tags"])
        return replace(transaction, **data)

    def _validate_criteria(self, criteria: SearchCriteria) -> None:
        if criteria.date_from:
            validate_date(criteria.date_from)
        if criteria.date_to:
            validate_date(criteria.date_to)
        if criteria.month:
            validate_month(criteria.month)
        if criteria.type:
            validate_type(criteria.type)

    def _matches(self, transaction: Transaction, criteria: SearchCriteria) -> bool:
        if criteria.month and not transaction.date.startswith(criteria.month):
            return False
        if criteria.date_from and transaction.date < criteria.date_from:
            return False
        if criteria.date_to and transaction.date > criteria.date_to:
            return False
        if criteria.category and transaction.category != criteria.category:
            return False
        if criteria.type and transaction.type != criteria.type:
            return False
        if criteria.query and criteria.query not in transaction.memo:
            return False
        if criteria.tag and criteria.tag not in (transaction.tags or []):
            return False
        return True
