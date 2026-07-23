from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    confidence: float | None = None


@dataclass
class Transcript:
    """STT output for a call recording."""

    call_id: UUID
    full_text: str
    segments: list[TranscriptSegment] = field(default_factory=list)
    stt_provider: str = ""
    stt_model: str = ""
    id: UUID = field(default_factory=uuid4)
