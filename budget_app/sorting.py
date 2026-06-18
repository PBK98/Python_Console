from __future__ import annotations

import heapq
import json
import os
import tempfile
from itertools import islice
from pathlib import Path
from typing import Iterable, Iterator

from budget_app.models import Transaction


CHUNK_SIZE = 1000


def transaction_sort_key(transaction: Transaction) -> tuple[str, int]:
    # 날짜가 같으면 id 번호가 큰 거래를 더 최신으로 본다.
    return transaction.date, _id_number(transaction.id)


def top_latest(transactions: Iterable[Transaction], limit: int) -> list[Transaction]:
    # list --limit은 전체 정렬 대신 최신 N개만 heap에 유지한다.
    return heapq.nlargest(limit, transactions, key=transaction_sort_key)


def iter_latest(transactions: Iterable[Transaction]) -> Iterator[Transaction]:
    chunk_paths: list[Path] = []
    iterator = iter(transactions)

    try:
        while True:
            # 전체 결과를 한 번에 정렬하지 않고 일정 크기씩 나누어 정렬한다.
            chunk = list(islice(iterator, CHUNK_SIZE))
            if not chunk:
                break
            chunk.sort(key=transaction_sort_key, reverse=True)
            chunk_paths.append(_write_chunk(chunk))

        chunk_iterators = [
            _iter_chunk(path, chunk_position)
            for chunk_position, path in enumerate(chunk_paths)
        ]
        # 이미 정렬된 chunk들을 병합하면 전체 최신순 결과를 순차적으로 만들 수 있다.
        for _, _, transaction in heapq.merge(*chunk_iterators):
            yield transaction
    finally:
        # 출력 중 오류가 나도 정렬용 임시 파일은 정리한다.
        for path in chunk_paths:
            path.unlink(missing_ok=True)


def _iter_chunk(
    path: Path,
    chunk_position: int,
) -> Iterator[tuple[tuple[int, int], tuple[int, int], Transaction]]:
    with path.open("r", encoding="utf-8") as file:
        for index, line in enumerate(file):
            transaction = Transaction.from_dict(json.loads(line))
            yield _merge_key(transaction), (chunk_position, index), transaction


def _write_chunk(transactions: list[Transaction]) -> Path:
    fd, temp_name = tempfile.mkstemp(prefix="budget-sort-", suffix=".jsonl", text=True)
    path = Path(temp_name)
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        for transaction in transactions:
            file.write(json.dumps(transaction.to_dict(), ensure_ascii=False) + "\n")
    return path


def _merge_key(transaction: Transaction) -> tuple[int, int]:
    # heapq.merge는 오름차순 병합이므로 음수 키로 최신순을 표현한다.
    date_number = int(transaction.date.replace("-", ""))
    return -date_number, -_id_number(transaction.id)


def _id_number(transaction_id: str) -> int:
    if transaction_id.startswith("TX-"):
        try:
            return int(transaction_id.replace("TX-", ""))
        except ValueError:
            return 0
    return 0
