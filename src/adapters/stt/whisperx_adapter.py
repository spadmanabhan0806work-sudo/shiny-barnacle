from __future__ import annotations

from pathlib import Path

from src.domain.services.language_detector import detect_language
from src.ports.stt_provider import TranscriptResult


class WhisperXSTTAdapter:
    """WhisperX speech-to-text adapter."""

    def __init__(
        self,
        *,
        model: str = "large-v3",
        device: str = "cpu",
        compute_type: str = "int8",
        batch_size: int = 8,
    ) -> None:
        self._model_name = model
        self._device = device
        self._compute_type = compute_type
        self._batch_size = batch_size
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            import whisperx
        except ImportError as exc:
            raise RuntimeError(
                "WhisperX is not installed. Install with: pip install whisperx "
                "or set STT_PROVIDER=mock for development."
            ) from exc

        self._model = whisperx.load_model(
            self._model_name,
            self._device,
            compute_type=self._compute_type,
        )
        return self._model

    async def transcribe(
        self, audio_path: Path, *, language: str | None = None
    ) -> TranscriptResult:
        import asyncio

        return await asyncio.to_thread(self._transcribe_sync, audio_path, language)

    def _transcribe_sync(
        self, audio_path: Path, language: str | None
    ) -> TranscriptResult:
        import whisperx

        model = self._load_model()
        audio = whisperx.load_audio(str(audio_path))
        result = model.transcribe(
            audio,
            batch_size=self._batch_size,
            language=language if language and language != "mixed" else None,
        )

        segments: list[dict] = []
        for seg in result.get("segments", []):
            segments.append(
                {
                    "start": seg.get("start", 0.0),
                    "end": seg.get("end", 0.0),
                    "text": seg.get("text", "").strip(),
                    "confidence": seg.get("avg_logprob"),
                }
            )

        full_text = " ".join(s["text"] for s in segments if s["text"]).strip()
        provider_lang = result.get("language", language or "unknown")
        detected = detect_language(full_text, provider_hint=provider_lang)

        return TranscriptResult(
            full_text=full_text,
            segments=segments,
            detected_language=detected,
            provider="whisperx",
            model=self._model_name,
        )
