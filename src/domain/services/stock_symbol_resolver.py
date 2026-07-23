from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path


@dataclass(frozen=True)
class SymbolMatch:
    symbol: str
    confidence: float
    matched_name: str = ""


class StockSymbolResolver:
    """Resolves spoken stock names to exchange symbols using master data."""

    def __init__(self, symbols_csv_path: Path) -> None:
        self._symbols: dict[str, str] = {}
        self._names: list[tuple[str, str]] = []
        self._load_symbols(symbols_csv_path)

    def _load_symbols(self, path: Path) -> None:
        if not path.exists():
            return
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        start = 1 if lines and lines[0].strip().lower().startswith("symbol") else 0
        for line in lines[start:]:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                symbol, name = parts[0].strip(), parts[1].strip().upper()
                self._symbols[name] = symbol
                self._symbols[symbol] = symbol
                self._names.append((name, symbol))

    def resolve(self, spoken_name: str) -> str | None:
        """Resolve a spoken stock name to its exchange symbol (exact match)."""
        match = self.resolve_fuzzy(spoken_name, min_confidence=1.0)
        return match.symbol if match else None

    def resolve_fuzzy(self, spoken_name: str, *, min_confidence: float = 0.6) -> SymbolMatch | None:
        """Fuzzy match spoken name against symbol registry."""
        normalized = spoken_name.strip().upper()
        if not normalized:
            return None

        if normalized in self._symbols:
            return SymbolMatch(symbol=self._symbols[normalized], confidence=1.0, matched_name=normalized)

        best_symbol = ""
        best_name = ""
        best_ratio = 0.0

        for name, symbol in self._names:
            ratio = SequenceMatcher(None, normalized, name).ratio()
            if normalized in name or name in normalized:
                ratio = max(ratio, 0.85)
            if ratio > best_ratio:
                best_ratio = ratio
                best_symbol = symbol
                best_name = name

        if best_ratio >= min_confidence:
            return SymbolMatch(symbol=best_symbol, confidence=best_ratio, matched_name=best_name)
        return None

    @property
    def symbol_count(self) -> int:
        return len(self._symbols)
