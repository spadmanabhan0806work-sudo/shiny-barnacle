from __future__ import annotations

from pathlib import Path

from src.domain.services.language_detector import detect_language
from src.ports.stt_provider import TranscriptResult


class GoogleSTTAdapter:
    """Google Cloud Speech-to-Text adapter."""

    def __init__(
        self,
        *,
        language_codes: list[str] | None = None,
        model: str = "latest_long",
        credentials_path: str | None = None,
    ) -> None:
        self._language_codes = language_codes or ["en-IN", "hi-IN", "ml-IN"]
        self._model = model
        self._credentials_path = credentials_path

    async def transcribe(
        self, audio_path: Path, *, language: str | None = None
    ) -> TranscriptResult:
        import asyncio

        return await asyncio.to_thread(self._transcribe_sync, audio_path, language)

    def _transcribe_sync(
        self, audio_path: Path, language: str | None
    ) -> TranscriptResult:
        try:
            from google.cloud import speech
        except ImportError as exc:
            raise RuntimeError(
                "google-cloud-speech is not installed. "
                "Install with: pip install google-cloud-speech"
            ) from exc

        client = speech.SpeechClient()
        content = audio_path.read_bytes()

        lang_codes = self._language_codes
        if language and language != "mixed":
            lang_map = {"en": "en-IN", "hi": "hi-IN", "ml": "ml-IN"}
            lang_codes = [lang_map.get(language, f"{language}-IN")]

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=lang_codes[0],
            alternative_language_codes=lang_codes[1:] if len(lang_codes) > 1 else [],
            enable_automatic_punctuation=True,
            model=self._model,
        )
        audio = speech.RecognitionAudio(content=content)
        response = client.recognize(config=config, audio=audio)

        segments: list[dict] = []
        full_parts: list[str] = []
        for result in response.results:
            alt = result.alternatives[0]
            full_parts.append(alt.transcript.strip())
            if result.result_end_time:
                end_sec = (
                    result.result_end_time.seconds
                    + result.result_end_time.microseconds / 1_000_000
                )
            else:
                end_sec = 0.0
            segments.append(
                {
                    "start": 0.0,
                    "end": end_sec,
                    "text": alt.transcript.strip(),
                    "confidence": alt.confidence,
                }
            )

        full_text = " ".join(full_parts).strip()
        detected = detect_language(full_text)

        return TranscriptResult(
            full_text=full_text,
            segments=segments,
            detected_language=detected,
            provider="google",
            model=self._model,
        )
