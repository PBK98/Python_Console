from __future__ import annotations

from datetime import datetime

from budget_app.errors import ValidationError


VALID_TYPES = {"income", "expense"}


def validate_date(value: str) -> str:
    # datetime.strptime을 사용하면 존재하지 않는 날짜도 함께 걸러낼 수 있다.
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as error:
        raise ValidationError(
            "날짜 형식이 올바르지 않습니다.",
            "예: 2024-01-15",
        ) from error
    return value


def validate_month(value: str) -> str:
    # summary와 budget은 월 단위 기능이므로 YYYY-MM만 허용한다.
    try:
        datetime.strptime(value, "%Y-%m")
    except ValueError as error:
        raise ValidationError(
            "월 형식이 올바르지 않습니다.",
            "예: 2024-01",
        ) from error
    return value


def validate_amount(value: str | int) -> int:
    # CLI 입력은 문자열로 들어오므로 서비스에서 쓰기 전에 int로 변환한다.
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
    # 수입과 지출 외의 값이 저장되면 요약 계산이 틀어질 수 있다.
    if value not in VALID_TYPES:
        raise ValidationError(
            "거래 타입이 올바르지 않습니다.",
            "income 또는 expense 중 하나를 입력하세요.",
        )
    return value


def parse_tags(value: str | None) -> list[str]:
    # "meal,work" 형태의 CLI/CSV 입력을 내부 리스트 구조로 변환한다.
    if not value:
        return []
    return [tag.strip() for tag in value.split(",") if tag.strip()]
