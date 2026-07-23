from enum import Enum


class TradeSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

    @classmethod
    def from_string(cls, value: str) -> "TradeSide":
        normalized = value.upper().strip()
        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(f"Invalid trade side: {value}") from exc
