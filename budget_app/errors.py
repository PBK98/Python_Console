from __future__ import annotations


class AppError(Exception):
    """Base exception for user-facing application errors."""

    def __init__(self, message: str, hint: str | None = None) -> None:
        # message는 원인, hint는 사용자가 다음에 시도할 해결 방법으로 출력된다.
        super().__init__(message)
        self.message = message
        self.hint = hint


class ValidationError(AppError):
    """Raised when user input or imported data is invalid."""


class NotFoundError(AppError):
    """Raised when requested data does not exist."""
