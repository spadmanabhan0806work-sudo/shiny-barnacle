from __future__ import annotations

from pathlib import Path

from src.domain.services.language_detector import detect_language
from src.ports.stt_provider import TranscriptResult


class MockSTTAdapter:
    """Deterministic STT adapter for dev/test without GPU."""

    def __init__(
        self,
        *,
        default_language: str = "en",
        model: str = "mock-v1",
    ) -> None:
        self._default_language = default_language
        self._model = model

    async def transcribe(
        self, audio_path: Path, *, language: str | None = None
    ) -> TranscriptResult:
        full_text = (
            "I want to buy one hundred shares of Reliance at twenty five hundred rupees on NSE."
        )
        if language == "hi":
            full_text = "मुझे NSE पर Reliance के सौ शेयर खरीदने हैं।"
        elif language == "ml":
            full_text = "എനിക്ക് NSE ൽ Reliance ന്റെ നൂറ് ഷെയറുകൾ വാങ്ങണം."
        elif language == "mixed":
            full_text = "Mujhe NSE par Reliance ke sau shares buy karne hain at 2500."

        detected = language or detect_language(full_text, provider_hint=self._default_language)
        segments = [
            {
                "start": 0.0,
                "end": 5.0,
                "text": full_text,
                "confidence": 0.95,
            }
        ]
        return TranscriptResult(
            full_text=full_text,
            segments=segments,
            detected_language=detected,
            provider="mock",
            model=self._model,
        )
