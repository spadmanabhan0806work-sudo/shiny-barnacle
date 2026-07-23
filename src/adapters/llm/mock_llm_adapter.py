from __future__ import annotations

import re

from src.domain.services.numeric_parser import NumericParser
from src.ports.llm_provider import StructuredExtractionResult


class MockLLMAdapter:
    """Deterministic LLM adapter for dev/test — parses transcript into structured intent."""

    def __init__(self, *, model: str = "mock-llm-v1") -> None:
        self._model = model
        self._numeric = NumericParser()

    async def extract_structured(
        self,
        transcript: str,
        schema: dict,
        *,
        prompt_version: str,
    ) -> StructuredExtractionResult:
        side = self._extract_side(transcript)
        stock = self._extract_stock(transcript)
        quantity = self._extract_quantity(transcript)
        price = self._extract_price(transcript)
        exchange = self._extract_exchange(transcript)

        data = {
            "side": side,
            "stock_symbol": stock,
            "quantity": quantity,
            "price": price,
            "exchange": exchange,
            "confidence": 0.92,
        }
        return StructuredExtractionResult(
            data=data,
            confidence=data["confidence"],
            provider="mock",
            model=self._model,
            raw_output={"parsed_from_transcript": True, **data},
        )

    def _extract_side(self, text: str) -> str:
        lower = text.lower()
        if re.search(r"\b(sell|बेच|വിൽപ്പന|bech)\b", lower):
            return "SELL"
        return "BUY"

    def _extract_stock(self, text: str) -> str:
        match = re.search(
            r"\b(?:of|के|ke|ന്റെ|of)\s+([A-Za-z\u0900-\u097F\u0D00-\u0D7F]+)",
            text,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
        for known in ("Reliance", "TCS", "Infosys", "HDFC", "ICICI", "SBI"):
            if known.lower() in text.lower():
                return known
        return "UNKNOWN"

    def _extract_quantity(self, text: str) -> int:
        digit_match = re.search(r"\b(\d+)\s*(?:shares?|शेयर|ഷെയർ|sau)\b", text, re.IGNORECASE)
        if digit_match:
            return int(digit_match.group(1))

        word_patterns = [
            r"\b(one hundred|hundred|सौ|നൂറ്|sau)\b",
            r"\b(fifty|पचास|അമ്പത്|pachaas|pachas)\b",
        ]
        for pattern in word_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parsed = self._numeric.parse_int(match.group(1))
                if parsed:
                    return parsed
        return 100

    def _extract_price(self, text: str) -> float:
        digit_match = re.search(
            r"(?:at|@|पर|₹|rs\.?|rupees?)\s*([\d,]+(?:\.\d+)?)",
            text,
            re.IGNORECASE,
        )
        if digit_match:
            val = self._numeric.parse_decimal(digit_match.group(1))
            return float(val) if val else 2500.0

        word_match = re.search(
            r"(?:at|@|पर)\s+((?:twenty|thirty|forty|fifty|hundred|\w+)(?:\s+(?:five|hundred|thousand|\w+))*)",
            text,
            re.IGNORECASE,
        )
        if word_match:
            parsed = self._numeric.parse_int(word_match.group(1))
            if parsed:
                return float(parsed)
        if re.search(r"\b2500\b", text):
            return 2500.0
        return 2500.0

    def _extract_exchange(self, text: str) -> str:
        upper = text.upper()
        if "BSE" in upper:
            return "BSE"
        return "NSE"
