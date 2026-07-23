from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class IntentExtraction:
    """Structured trading intent extracted from a transcript."""

    call_id: UUID
    side: str
    stock_symbol: str
    quantity: int
    price: float
    exchange: str
    confidence: float
    prompt_version: str = ""
    llm_provider: str = ""
    raw_llm_output: dict | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
