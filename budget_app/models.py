from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Transaction:
    # 거래 1건을 표현하는 내부 표준 형태다.
    id: str
    date: str
    type: str
    category: str
    amount: int
    memo: str = ""
    tags: list[str] | None = None

    def to_dict(self) -> dict[str, object]:
        # JSONL에 저장하기 전에 dataclass를 직렬화 가능한 dict로 바꾼다.
        data = asdict(self)
        data["tags"] = self.tags or []
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Transaction":
        # 파일에서 읽은 dict는 타입이 느슨하므로 모델 생성 시 필요한 타입으로 맞춘다.
        raw_tags = data.get("tags", [])
        tags = raw_tags if isinstance(raw_tags, list) else []
        return cls(
            id=str(data["id"]),
            date=str(data["date"]),
            type=str(data["type"]),
            category=str(data["category"]),
            amount=int(data["amount"]),
            memo=str(data.get("memo", "")),
            tags=[str(tag) for tag in tags],
        )


@dataclass
class Budget:
    # 월별 예산은 YYYY-MM 형태의 month와 양수 amount만 저장한다.
    month: str
    amount: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Budget":
        return cls(month=str(data["month"]), amount=int(data["amount"]))


@dataclass
class SearchCriteria:
    # CLI 옵션을 서비스 계층으로 넘길 때 사용하는 검색 조건 묶음이다.
    date_from: str | None = None
    date_to: str | None = None
    category: str | None = None
    type: str | None = None
    query: str | None = None
    tag: str | None = None
    month: str | None = None
