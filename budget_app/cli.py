from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Iterable

from budget_app.decorators import handle_errors, measure_time
from budget_app.models import Budget, SearchCriteria, Transaction
from budget_app.repositories import BudgetRepository, CategoryRepository, JsonlStore, TransactionRepository
from budget_app.services import BudgetService, CategoryService, TransactionService


@dataclass
class AppServices:
    transactions: TransactionService
    categories: CategoryService
    budgets: BudgetService


class ParserBuilder:
    """CLI 명령어와 옵션을 구성하는 책임만 맡는다."""

    def build(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="python -m budget_app")
        parser.add_argument("--data-dir", default="./data", help="저장 파일 디렉토리")

        # add/list/search 같은 1단계 명령어는 args.command에 저장된다.
        subparsers = parser.add_subparsers(dest="command", required=True)

        subparsers.add_parser("add", help="거래 추가")
        self.add_list_parser(subparsers)
        self.add_search_parser(subparsers)
        self.add_summary_parser(subparsers)
        self.add_budget_parser(subparsers)
        self.add_category_parser(subparsers)
        self.add_update_parser(subparsers)
        self.add_delete_parser(subparsers)
        self.add_import_parser(subparsers)
        self.add_export_parser(subparsers)

        return parser

    def add_list_parser(self, subparsers) -> None:
        list_parser = subparsers.add_parser("list", help="거래 목록")
        list_parser.add_argument("--limit", type=int, default=10)

    def add_search_parser(self, subparsers) -> None:
        search_parser = subparsers.add_parser("search", help="거래 검색")
        self.add_search_options(search_parser)

    def add_summary_parser(self, subparsers) -> None:
        summary_parser = subparsers.add_parser("summary", help="월별 요약")
        summary_parser.add_argument("--month", required=True)
        summary_parser.add_argument("--top", type=int, default=3)

    def add_budget_parser(self, subparsers) -> None:
        budget_parser = subparsers.add_parser("budget", help="예산 관리")
        # budget set/list/show처럼 한 번 더 나뉘는 명령어는 별도 subparser를 둔다.
        budget_subparsers = budget_parser.add_subparsers(dest="budget_command", required=True)
        budget_set_parser = budget_subparsers.add_parser("set", help="월 예산 설정")
        budget_set_parser.add_argument("--month", required=True)
        budget_set_parser.add_argument("--amount", required=True)
        budget_subparsers.add_parser("list", help="예산 목록")
        budget_show_parser = budget_subparsers.add_parser("show", help="월 예산 조회")
        budget_show_parser.add_argument("--month", required=True)

    def add_category_parser(self, subparsers) -> None:
        category_parser = subparsers.add_parser("category", help="카테고리 관리")
        category_subparsers = category_parser.add_subparsers(
            dest="category_command",
            required=True,
        )
        category_subparsers.add_parser("list", help="카테고리 목록")
        category_subparsers.add_parser("add", help="카테고리 추가")
        category_remove_parser = category_subparsers.add_parser("remove", help="카테고리 삭제")
        category_remove_parser.add_argument("--name", required=True)

    def add_update_parser(self, subparsers) -> None:
        update_parser = subparsers.add_parser("update", help="거래 수정")
        update_parser.add_argument("--id", required=True)
        update_parser.add_argument("--date")
        update_parser.add_argument("--type")
        update_parser.add_argument("--category")
        update_parser.add_argument("--amount")
        update_parser.add_argument("--memo")
        update_parser.add_argument("--tags")

    def add_delete_parser(self, subparsers) -> None:
        delete_parser = subparsers.add_parser("delete", help="거래 삭제")
        delete_parser.add_argument("--id", required=True)

    def add_import_parser(self, subparsers) -> None:
        import_parser = subparsers.add_parser("import", help="CSV 가져오기")
        import_parser.add_argument("--from", dest="input_path", required=True)

    def add_export_parser(self, subparsers) -> None:
        export_parser = subparsers.add_parser("export", help="CSV 내보내기")
        export_parser.add_argument("--out", required=True)
        self.add_search_options(export_parser)

    def add_search_options(self, parser: argparse.ArgumentParser) -> None:
        # search와 export가 같은 필터 옵션을 쓰므로 중복 등록을 피한다.
        parser.add_argument("--from", dest="date_from")
        parser.add_argument("--to", dest="date_to")
        parser.add_argument("--category")
        parser.add_argument("--type")
        parser.add_argument("--q", dest="query")
        parser.add_argument("--tag")
        parser.add_argument("--month")


class ServiceFactory:
    """Repository와 service 객체를 조립한다."""

    def build(self, data_dir: str) -> AppServices:
        store = JsonlStore(data_dir)
        transaction_repository = TransactionRepository(store)
        category_repository = CategoryRepository(store)
        budget_repository = BudgetRepository(store)
        category_service = CategoryService(category_repository, transaction_repository)
        budget_service = BudgetService(budget_repository)
        transaction_service = TransactionService(
            transaction_repository,
            category_service,
            budget_repository,
        )
        return AppServices(
            transactions=transaction_service,
            categories=category_service,
            budgets=budget_service,
        )


class ConsolePrinter:
    """콘솔 출력 형식을 한곳에서 관리한다."""

    def print_transactions(self, transactions: Iterable[Transaction]) -> None:
        # Iterable을 그대로 순회하므로 search 결과 제너레이터도 바로 출력할 수 있다.
        printed = False
        for transaction in transactions:
            printed = True
            tags = ",".join(transaction.tags or [])
            print(
                f"{transaction.id} | {transaction.date} | {transaction.type:<7} | "
                f"{transaction.category} | {transaction.amount} | {transaction.memo} | {tags}"
            )
        if not printed:
            print("데이터 없음")

    def print_budgets(self, budgets: Iterable[Budget]) -> None:
        printed = False
        for budget in budgets:
            printed = True
            self.print_budget(budget)
        if not printed:
            print("데이터 없음")

    def print_budget(self, budget: Budget) -> None:
        print(f"{budget.month} | {budget.amount}원")


class CommandRunner:
    """파싱된 args를 실제 service 호출로 연결한다."""

    def __init__(
        self,
        service_factory: ServiceFactory | None = None,
        printer: ConsolePrinter | None = None,
    ) -> None:
        self.service_factory = service_factory or ServiceFactory()
        self.printer = printer or ConsolePrinter()

    def run(self, args: argparse.Namespace) -> int:
        services = self.service_factory.build(args.data_dir)

        if args.command == "add":
            return self.run_add(services.transactions)
        if args.command == "list":
            return self.run_list(services.transactions, args.limit)
        if args.command == "search":
            return self.run_search(services.transactions, args)
        if args.command == "summary":
            return self.run_summary(services.transactions, args.month, args.top)
        if args.command == "budget":
            return self.run_budget(services.budgets, args)
        if args.command == "category":
            return self.run_category(services.categories, args)
        if args.command == "update":
            return self.run_update(services.transactions, args)
        if args.command == "delete":
            services.transactions.delete_transaction(args.id)
            print(f"[삭제 완료] id={args.id}")
            return 0
        if args.command == "import":
            imported, skipped = services.transactions.import_csv(args.input_path)
            print(f"[완료] imported={imported}, skipped={skipped}")
            return 0
        if args.command == "export":
            count = services.transactions.export_csv(args.out, self.criteria_from_args(args))
            print(f"[완료] {args.out} ({count} records)")
            return 0

        return 1

    def run_add(self, service: TransactionService) -> int:
        # add는 과제 요구사항에 맞춰 대화형 입력으로 처리한다.
        date = input("날짜(YYYY-MM-DD): ").strip()
        type_ = input("타입(income/expense): ").strip()
        category = input("카테고리: ").strip()
        amount = input("금액(양수): ").strip()
        memo = input("메모(선택): ").strip()
        tags = input("태그(쉼표로 구분, 없으면 엔터): ").strip()
        transaction = service.add_transaction(date, type_, category, amount, memo, tags)
        print(f"[저장 완료] id={transaction.id}")
        return 0

    def run_list(self, service: TransactionService, limit: int) -> int:
        transactions = service.list_transactions(limit)
        self.printer.print_transactions(transactions)
        return 0

    def run_search(self, service: TransactionService, args: argparse.Namespace) -> int:
        transactions = service.search(self.criteria_from_args(args))
        self.printer.print_transactions(transactions)
        return 0

    def run_summary(self, service: TransactionService, month: str, top: int) -> int:
        summary = service.summarize(month, top)
        if summary["count"] == 0:
            print("데이터 없음")
            return 0

        print(f"총 수입: {summary['total_income']}원")
        print(f"총 지출: {summary['total_expense']}원")
        print(f"잔액: {summary['balance']}원")

        budget = summary["budget"]
        if budget:
            print(f"예산: {budget.amount}원 (사용률 {summary['usage_rate']:.1f}%)")
            if summary["is_over_budget"]:
                print("[경고] 예산을 초과했습니다.")

        print()
        print("지출 TOP")
        for index, (category, amount) in enumerate(summary["top_categories"], start=1):
            print(f"{index}) {category} {amount}원")
        return 0

    def run_budget(self, service: BudgetService, args: argparse.Namespace) -> int:
        if args.budget_command == "set":
            budget = service.set_budget(args.month, args.amount)
            print(f"[저장 완료] {budget.month} 예산 {budget.amount}원")
            return 0
        if args.budget_command == "list":
            self.printer.print_budgets(service.list_budgets())
            return 0
        if args.budget_command == "show":
            budget = service.show_budget(args.month)
            if budget is None:
                print("데이터 없음")
                return 0
            self.printer.print_budget(budget)
            return 0
        return 1

    def run_category(self, service: CategoryService, args: argparse.Namespace) -> int:
        if args.category_command == "list":
            for category in service.list_categories():
                print(f"- {category}")
            return 0
        if args.category_command == "add":
            name = input("카테고리명: ").strip()
            service.add_category(name)
            print(f"[저장 완료] category={name}")
            return 0
        if args.category_command == "remove":
            service.remove_category(args.name)
            print(f"[삭제 완료] category={args.name}")
            return 0
        return 1

    def run_update(self, service: TransactionService, args: argparse.Namespace) -> int:
        transaction = service.update_transaction(
            args.id,
            {
                "date": args.date,
                "type": args.type,
                "category": args.category,
                "amount": args.amount,
                "memo": args.memo,
                "tags": args.tags,
            },
        )
        print(f"[수정 완료] id={transaction.id}")
        return 0

    def criteria_from_args(self, args: argparse.Namespace) -> SearchCriteria:
        # argparse 결과를 서비스 계층에서 쓰기 좋은 검색 조건 객체로 변환한다.
        return SearchCriteria(
            date_from=getattr(args, "date_from", None),
            date_to=getattr(args, "date_to", None),
            category=getattr(args, "category", None),
            type=getattr(args, "type", None),
            query=getattr(args, "query", None),
            tag=getattr(args, "tag", None),
            month=getattr(args, "month", None),
        )


def build_parser() -> argparse.ArgumentParser:
    return ParserBuilder().build()


@handle_errors
@measure_time
def run(args: argparse.Namespace) -> int:
    return CommandRunner().run(args)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)
