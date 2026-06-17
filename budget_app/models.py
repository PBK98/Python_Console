from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Transaction:
    id: str
    date: str
    type: str
    category: str
    amount: int
    memo: str = ""
    tags: list[str] | None = None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["tags"] = self.tags or []
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Transaction":
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
    month: str
    amount: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Budget":
        return cls(month=str(data["month"]), amount=int(data["amount"]))


@dataclass
class SearchCriteria:
    date_from: str | None = None
    date_to: str | None = None
    category: str | None = None
    type: str | None = None
    query: str | None = None
    tag: str | None = None
    month: str | None = None

