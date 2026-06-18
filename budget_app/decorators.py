from __future__ import annotations

import csv
import json
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
        except FileNotFoundError as error:
            print("[오류] 파일을 찾을 수 없습니다.")
            print(f"[힌트] 경로를 확인하세요: {error.filename}")
            return 1
        except PermissionError as error:
            print("[오류] 파일 접근 권한이 없습니다.")
            print(f"[힌트] 권한 또는 경로를 확인하세요: {error.filename}")
            return 1
        except json.JSONDecodeError:
            print("[오류] 저장 파일의 JSONL 형식이 올바르지 않습니다.")
            print("[힌트] data 디렉토리의 저장 파일 내용을 확인하세요.")
            return 1
        except csv.Error:
            print("[오류] CSV 파일 형식이 올바르지 않습니다.")
            print("[힌트] UTF-8, 헤더 포함, 쉼표 구분 형식인지 확인하세요.")
            return 1
        except EOFError:
            print("[오류] 입력이 중단되었습니다.")
            print("[힌트] 필요한 값을 끝까지 입력하세요.")
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
