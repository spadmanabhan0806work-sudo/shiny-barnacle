from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4


class AnnotationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    VERIFIED = "verified"


@dataclass
class GroundTruth:
    """Human-labeled intent fields for a call."""

    side: str
    stock_symbol: str
    quantity: int
    price: float
    exchange: str

    def __post_init__(self) -> None:
        if self.side not in ("BUY", "SELL"):
            raise ValueError(f"Invalid trade side: {self.side}")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if self.exchange not in ("NSE", "BSE"):
            raise ValueError(f"Invalid exchange: {self.exchange}")


@dataclass
class Annotation:
    """Human annotation linking ground truth to a call recording."""

    call_id: UUID
    annotator_id: str
    ground_truth: GroundTruth
    status: AnnotationStatus = AnnotationStatus.DRAFT
    id: UUID = field(default_factory=uuid4)

    def submit(self) -> None:
        self.status = AnnotationStatus.SUBMITTED

    def verify(self) -> None:
        self.status = AnnotationStatus.VERIFIED
