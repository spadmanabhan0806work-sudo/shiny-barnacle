from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4


class CallStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    TRANSCRIBED = "transcribed"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    REVIEW_REQUIRED = "review_required"
    FAILED = "failed"


@dataclass
class CallRecording:
    """Aggregate root for a customer call recording."""

    tenant_id: str
    storage_key: str
    status: CallStatus = CallStatus.PENDING
    detected_language: str | None = None
    duration_sec: float | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def mark_processing(self) -> None:
        self.status = CallStatus.PROCESSING

    def mark_transcribed(self) -> None:
        self.status = CallStatus.TRANSCRIBED

    def mark_extracting(self) -> None:
        self.status = CallStatus.EXTRACTING

    def mark_completed(self) -> None:
        self.status = CallStatus.COMPLETED

    def mark_review_required(self) -> None:
        self.status = CallStatus.REVIEW_REQUIRED

    def mark_failed(self) -> None:
        self.status = CallStatus.FAILED
