from __future__ import annotations

from functools import wraps
from time import perf_counter
from typing import Callable, TypeVar

from budget_app.errors import AppError


F = TypeVar("F", bound=Callable[..., int])


def handle_errors(func: F) -> F:
    @wraps(func)
    def wrapper(*args, **kwargs) -> int:
        try:
            return func(*args, **kwargs)
        except AppError as error:
            print(f"[오류] {error.message}")
            if error.hint:
                print(f"[힌트] {error.hint}")
            return 1

    return wrapper  # type: ignore[return-value]


def measure_time(func: F) -> F:
    @wraps(func)
    def wrapper(*args, **kwargs) -> int:
        started_at = perf_counter()
        result = func(*args, **kwargs)
        elapsed = perf_counter() - started_at
        print(f"[실행 시간] {elapsed:.3f}s")
        return result

    return wrapper  # type: ignore[return-value]

