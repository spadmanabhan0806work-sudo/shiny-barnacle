from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CORRECTED = "corrected"
    REJECTED = "rejected"


@dataclass
class ReviewQueueItem:
    """Human-in-the-loop review item for low-confidence extractions."""

    extraction_id: UUID
    status: ReviewStatus = ReviewStatus.PENDING
    corrected_fields: dict | None = None
    reviewer_id: str | None = None
    id: UUID = field(default_factory=uuid4)

    def approve(self, reviewer_id: str) -> None:
        self.status = ReviewStatus.APPROVED
        self.reviewer_id = reviewer_id

    def correct(self, reviewer_id: str, fields: dict) -> None:
        self.status = ReviewStatus.CORRECTED
        self.reviewer_id = reviewer_id
        self.corrected_fields = fields
