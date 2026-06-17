from __future__ import annotations

from datetime import datetime

from budget_app.errors import ValidationError


VALID_TYPES = {"income", "expense"}


def validate_date(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as error:
        raise ValidationError(
            "날짜 형식이 올바르지 않습니다.",
            "예: 2024-01-15",
        ) from error
    return value


def validate_month(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m")
    except ValueError as error:
        raise ValidationError(
            "월 형식이 올바르지 않습니다.",
            "예: 2024-01",
        ) from error
    return value


def validate_amount(value: str | int) -> int:
    try:
        amount = int(value)
    except ValueError as error:
        raise ValidationError(
            "금액은 정수여야 합니다.",
            "예: 15000",
        ) from error

    if amount <= 0:
        raise ValidationError(
            "금액은 0보다 커야 합니다.",
            "양수 금액을 입력하세요.",
        )
    return amount


def validate_type(value: str) -> str:
    if value not in VALID_TYPES:
        raise ValidationError(
            "거래 타입이 올바르지 않습니다.",
            "income 또는 expense 중 하나를 입력하세요.",
        )
    return value


def parse_tags(value: str | None) -> list[str]:
    if not value:
        return []
    return [tag.strip() for tag in value.split(",") if tag.strip()]

