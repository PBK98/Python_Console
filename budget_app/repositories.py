from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Iterator

from budget_app.models import Budget, Transaction


DEFAULT_CATEGORIES = ["food", "transport", "rent", "salary", "etc"]


class JsonlStore:
    def __init__(self, data_dir: str = "./data") -> None:
        self.data_dir = Path(data_dir)
        self.transactions_path = self.data_dir / "transactions.jsonl"
        self.categories_path = self.data_dir / "categories.jsonl"
        self.budgets_path = self.data_dir / "budgets.jsonl"

    def initialize(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        for path in (self.transactions_path, self.categories_path, self.budgets_path):
            path.touch(exist_ok=True)
        if self.categories_path.stat().st_size == 0:
            with self.categories_path.open("w", encoding="utf-8") as file:
                for category in DEFAULT_CATEGORIES:
                    file.write(json.dumps({"name": category}, ensure_ascii=False) + "\n")


class TransactionRepository:
    def __init__(self, store: JsonlStore) -> None:
        self.store = store

    def iter_all(self) -> Iterator[Transaction]:
        self.store.initialize()
        with self.store.transactions_path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    yield Transaction.from_dict(json.loads(line))

    def append(self, transaction: Transaction) -> None:
        self.store.initialize()
        with self.store.transactions_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(transaction.to_dict(), ensure_ascii=False) + "\n")

    def rewrite(self, transactions: list[Transaction]) -> None:
        self.store.initialize()
        directory = self.store.transactions_path.parent
        fd, temp_name = tempfile.mkstemp(dir=directory, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
                for transaction in transactions:
                    temp_file.write(json.dumps(transaction.to_dict(), ensure_ascii=False) + "\n")
            os.replace(temp_name, self.store.transactions_path)
        except Exception:
            Path(temp_name).unlink(missing_ok=True)
            raise


class CategoryRepository:
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
            for category in sorted(set(categories)):
                file.write(json.dumps({"name": category}, ensure_ascii=False) + "\n")


class BudgetRepository:
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
        budgets = [item for item in self.list_all() if item.month != budget.month]
        budgets.append(budget)
        with self.store.budgets_path.open("w", encoding="utf-8") as file:
            for item in sorted(budgets, key=lambda value: value.month):
                file.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")
