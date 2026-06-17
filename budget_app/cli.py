from __future__ import annotations

import argparse

from budget_app.decorators import handle_errors, measure_time
from budget_app.models import SearchCriteria, Transaction
from budget_app.repositories import BudgetRepository, CategoryRepository, JsonlStore, TransactionRepository
from budget_app.services import BudgetService, CategoryService, TransactionService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m budget_app")
    parser.add_argument("--data-dir", default="./data", help="저장 파일 디렉토리")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("add", help="거래 추가")

    list_parser = subparsers.add_parser("list", help="거래 목록")
    list_parser.add_argument("--limit", type=int, default=10)

    search_parser = subparsers.add_parser("search", help="거래 검색")
    add_search_options(search_parser)

    summary_parser = subparsers.add_parser("summary", help="월별 요약")
    summary_parser.add_argument("--month", required=True)
    summary_parser.add_argument("--top", type=int, default=3)

    budget_parser = subparsers.add_parser("budget", help="예산 관리")
    budget_subparsers = budget_parser.add_subparsers(dest="budget_command", required=True)
    budget_set_parser = budget_subparsers.add_parser("set", help="월 예산 설정")
    budget_set_parser.add_argument("--month", required=True)
    budget_set_parser.add_argument("--amount", required=True)

    category_parser = subparsers.add_parser("category", help="카테고리 관리")
    category_subparsers = category_parser.add_subparsers(dest="category_command", required=True)
    category_subparsers.add_parser("list", help="카테고리 목록")
    category_subparsers.add_parser("add", help="카테고리 추가")
    category_remove_parser = category_subparsers.add_parser("remove", help="카테고리 삭제")
    category_remove_parser.add_argument("--name", required=True)

    update_parser = subparsers.add_parser("update", help="거래 수정")
    update_parser.add_argument("--id", required=True)
    update_parser.add_argument("--date")
    update_parser.add_argument("--type")
    update_parser.add_argument("--category")
    update_parser.add_argument("--amount")
    update_parser.add_argument("--memo")
    update_parser.add_argument("--tags")

    delete_parser = subparsers.add_parser("delete", help="거래 삭제")
    delete_parser.add_argument("--id", required=True)

    import_parser = subparsers.add_parser("import", help="CSV 가져오기")
    import_parser.add_argument("--from", dest="input_path", required=True)

    export_parser = subparsers.add_parser("export", help="CSV 내보내기")
    export_parser.add_argument("--out", required=True)
    add_search_options(export_parser)

    return parser


def add_search_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--from", dest="date_from")
    parser.add_argument("--to", dest="date_to")
    parser.add_argument("--category")
    parser.add_argument("--type")
    parser.add_argument("--q", dest="query")
    parser.add_argument("--tag")
    parser.add_argument("--month")


@handle_errors
@measure_time
def run(args: argparse.Namespace) -> int:
    store = JsonlStore(args.data_dir)
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

    if args.command == "add":
        return run_add(transaction_service)
    if args.command == "list":
        return run_list(transaction_service, args.limit)
    if args.command == "search":
        return run_search(transaction_service, args)
    if args.command == "summary":
        return run_summary(transaction_service, args.month, args.top)
    if args.command == "budget":
        return run_budget(budget_service, args)
    if args.command == "category":
        return run_category(category_service, args)
    if args.command == "update":
        return run_update(transaction_service, args)
    if args.command == "delete":
        transaction_service.delete_transaction(args.id)
        print(f"[삭제 완료] id={args.id}")
        return 0
    if args.command == "import":
        imported, skipped = transaction_service.import_csv(args.input_path)
        print(f"[완료] imported={imported}, skipped={skipped}")
        return 0
    if args.command == "export":
        count = transaction_service.export_csv(args.out, criteria_from_args(args))
        print(f"[완료] {args.out} ({count} records)")
        return 0

    return 1


def run_add(service: TransactionService) -> int:
    date = input("날짜(YYYY-MM-DD): ").strip()
    type_ = input("타입(income/expense): ").strip()
    category = input("카테고리: ").strip()
    amount = input("금액(양수): ").strip()
    memo = input("메모(선택): ").strip()
    tags = input("태그(쉼표로 구분, 없으면 엔터): ").strip()
    transaction = service.add_transaction(date, type_, category, amount, memo, tags)
    print(f"[저장 완료] id={transaction.id}")
    return 0


def run_list(service: TransactionService, limit: int) -> int:
    transactions = service.list_transactions(limit)
    print_transactions(transactions)
    return 0


def run_search(service: TransactionService, args: argparse.Namespace) -> int:
    transactions = service.search(criteria_from_args(args))
    print_transactions(transactions)
    return 0


def run_summary(service: TransactionService, month: str, top: int) -> int:
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


def run_budget(service: BudgetService, args: argparse.Namespace) -> int:
    if args.budget_command == "set":
        budget = service.set_budget(args.month, args.amount)
        print(f"[저장 완료] {budget.month} 예산 {budget.amount}원")
        return 0
    return 1


def run_category(service: CategoryService, args: argparse.Namespace) -> int:
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


def run_update(service: TransactionService, args: argparse.Namespace) -> int:
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


def criteria_from_args(args: argparse.Namespace) -> SearchCriteria:
    return SearchCriteria(
        date_from=getattr(args, "date_from", None),
        date_to=getattr(args, "date_to", None),
        category=getattr(args, "category", None),
        type=getattr(args, "type", None),
        query=getattr(args, "query", None),
        tag=getattr(args, "tag", None),
        month=getattr(args, "month", None),
    )


def print_transactions(transactions: list[Transaction]) -> None:
    if not transactions:
        print("데이터 없음")
        return
    for transaction in transactions:
        tags = ",".join(transaction.tags or [])
        print(
            f"{transaction.id} | {transaction.date} | {transaction.type:<7} | "
            f"{transaction.category} | {transaction.amount} | {transaction.memo} | {tags}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)

