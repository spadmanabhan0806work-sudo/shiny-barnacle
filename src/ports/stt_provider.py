from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class TranscriptResult:
    full_text: str
    segments: list[dict]
    detected_language: str
    provider: str
    model: str


class SpeechToTextProvider(Protocol):
    async def transcribe(
        self, audio_path: Path, *, language: str | None = None
    ) -> TranscriptResult: ...
