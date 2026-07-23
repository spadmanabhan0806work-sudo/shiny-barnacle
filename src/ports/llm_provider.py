from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class StructuredExtractionResult:
    data: dict[str, Any]
    confidence: float
    provider: str
    model: str
    raw_output: dict[str, Any] | None = None


class LLMProvider(Protocol):
    async def extract_structured(
        self,
        transcript: str,
        schema: dict,
        *,
        prompt_version: str,
    ) -> StructuredExtractionResult: ...
