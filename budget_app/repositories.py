from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Iterable, Iterator

from budget_app.models import Budget, Transaction


DEFAULT_CATEGORIES = ["food", "transport", "rent", "salary", "etc"]


class JsonlStore:
    # 저장 경로를 한곳에서 관리해서 repository들이 같은 파일 위치를 공유한다.
    def __init__(self, data_dir: str = "./data") -> None:
        self.data_dir = Path(data_dir)
        self.transactions_path = self.data_dir / "transactions.jsonl"
        self.categories_path = self.data_dir / "categories.jsonl"
        self.budgets_path = self.data_dir / "budgets.jsonl"

    def initialize(self) -> None:
        # 첫 실행에서도 바로 사용할 수 있도록 저장 폴더와 파일을 준비한다.
        self.data_dir.mkdir(parents=True, exist_ok=True)
        for path in (self.transactions_path, self.categories_path, self.budgets_path):
            path.touch(exist_ok=True)
        if self.categories_path.stat().st_size == 0:
            with self.categories_path.open("w", encoding="utf-8") as file:
                for category in DEFAULT_CATEGORIES:
                    file.write(json.dumps({"name": category}, ensure_ascii=False) + "\n")


class TransactionRepository:
    # 거래 파일 입출력만 담당하고, 검색/요약 같은 의미 있는 로직은 service에 맡긴다.
    def __init__(self, store: JsonlStore) -> None:
        self.store = store

    def iter_all(self) -> Iterator[Transaction]:
        self.store.initialize()
        with self.store.transactions_path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    # yield로 한 줄씩 돌려주면 큰 파일도 필요한 만큼만 메모리에 올라간다.
                    yield Transaction.from_dict(json.loads(line))

    def append(self, transaction: Transaction) -> None:
        self.store.initialize()
        with self.store.transactions_path.open("a", encoding="utf-8") as file:
            # JSONL은 한 줄에 JSON 객체 하나를 저장하므로 append가 쉽다.
            file.write(json.dumps(transaction.to_dict(), ensure_ascii=False) + "\n")

    def rewrite(self, transactions: Iterable[Transaction]) -> None:
        self.store.initialize()
        directory = self.store.transactions_path.parent
        fd, temp_name = tempfile.mkstemp(dir=directory, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
                for transaction in transactions:
                    temp_file.write(json.dumps(transaction.to_dict(), ensure_ascii=False) + "\n")
            # 쓰기가 모두 성공한 뒤 한 번에 교체해서 파일이 반쯤만 저장되는 상황을 줄인다.
            os.replace(temp_name, self.store.transactions_path)
        except Exception:
            Path(temp_name).unlink(missing_ok=True)
            raise


class CategoryRepository:
    # 카테고리는 단순 문자열 목록이지만 파일 형식은 JSONL로 통일한다.
    def __init__(self, store: JsonlStore) -> None:
        self.store = store

    def list_all(self) -> list[str]:
        self.store.initialize()
        categories: list[str] = []
        with self.store.categories_path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    data = json.loads(line)
                    categories.append(str(data["name"]))
        return sorted(categories)

    def write_categories(self, categories: list[str]) -> None:
        self.store.initialize()
        with self.store.categories_path.open("w", encoding="utf-8") as file:
            # set으로 중복을 제거하고 정렬해서 매번 같은 순서로 저장한다.
            for category in sorted(set(categories)):
                file.write(json.dumps({"name": category}, ensure_ascii=False) + "\n")


class BudgetRepository:
    # 예산은 월별로 하나만 존재하도록 upsert 방식으로 저장한다.
    def __init__(self, store: JsonlStore) -> None:
        self.store = store

    def list_all(self) -> list[Budget]:
        self.store.initialize()
        budgets: list[Budget] = []
        with self.store.budgets_path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    budgets.append(Budget.from_dict(json.loads(line)))
        return budgets

    def find_by_month(self, month: str) -> Budget | None:
        for budget in self.list_all():
            if budget.month == month:
                return budget
        return None

    def upsert(self, budget: Budget) -> None:
        # 같은 month의 기존 예산을 제거한 뒤 새 예산을 추가한다.
        budgets = [item for item in self.list_all() if item.month != budget.month]
        budgets.append(budget)
        with self.store.budgets_path.open("w", encoding="utf-8") as file:
            for item in sorted(budgets, key=lambda value: value.month):
                file.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")
