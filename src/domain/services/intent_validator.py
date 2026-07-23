from __future__ import annotations

from dataclasses import dataclass

from src.domain.services.numeric_parser import NumericParser
from src.domain.services.stock_symbol_resolver import StockSymbolResolver, SymbolMatch
from src.domain.value_objects.trade_side import TradeSide


@dataclass
class ValidatedIntent:
    side: str
    stock_symbol: str
    quantity: int
    price: float
    exchange: str
    validation_notes: list[str]
    stock_match_confidence: float = 1.0


class IntentValidator:
    """Validate and normalize LLM-proposed intent fields."""

    def __init__(
        self,
        symbol_resolver: StockSymbolResolver,
        numeric_parser: NumericParser | None = None,
    ) -> None:
        self._resolver = symbol_resolver
        self._numeric = numeric_parser or NumericParser()

    def validate(self, raw: dict) -> ValidatedIntent:
        notes: list[str] = []

        side = self._normalize_side(raw.get("side"), notes)
        exchange = self._normalize_exchange(raw.get("exchange"), notes)
        quantity = self._normalize_quantity(raw.get("quantity"), notes)
        price = self._normalize_price(raw.get("price"), notes)
        stock_symbol, match_conf = self._normalize_stock(raw.get("stock_symbol"), notes)

        return ValidatedIntent(
            side=side,
            stock_symbol=stock_symbol,
            quantity=quantity,
            price=price,
            exchange=exchange,
            validation_notes=notes,
            stock_match_confidence=match_conf,
        )

    def _normalize_side(self, value: object, notes: list[str]) -> str:
        if value is None:
            notes.append("missing_side")
            return "BUY"
        try:
            return TradeSide.from_string(str(value)).value
        except ValueError:
            notes.append("invalid_side")
            return "BUY"

    def _normalize_exchange(self, value: object, notes: list[str]) -> str:
        if value is None:
            notes.append("missing_exchange")
            return "NSE"
        normalized = str(value).strip().upper()
        if normalized not in ("NSE", "BSE"):
            notes.append("invalid_exchange")
            return "NSE"
        return normalized

    def _normalize_quantity(self, value: object, notes: list[str]) -> int:
        parsed = self._numeric.parse_int(str(value)) if value is not None else None
        if parsed is None or parsed < 1:
            notes.append("invalid_quantity")
            return 1
        return parsed

    def _normalize_price(self, value: object, notes: list[str]) -> float:
        if value is None:
            notes.append("missing_price")
            return 0.0
        decimal_val = self._numeric.parse_decimal(str(value))
        if decimal_val is None or decimal_val < 0:
            notes.append("invalid_price")
            return 0.0
        return float(decimal_val)

    def _normalize_stock(self, value: object, notes: list[str]) -> tuple[str, float]:
        if value is None or not str(value).strip():
            notes.append("missing_stock")
            return "UNKNOWN", 0.0

        match: SymbolMatch | None = self._resolver.resolve_fuzzy(str(value))
        if match is None:
            notes.append("unknown_stock")
            return str(value).strip().upper(), 0.0
        if match.confidence < 1.0:
            notes.append("fuzzy_stock_match")
        return match.symbol, match.confidence
