from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from src.application.services.confidence_router import ConfidenceRouter
from src.domain.entities.intent_extraction import IntentExtraction
from src.domain.entities.review_queue_item import ReviewQueueItem
from src.domain.entities.transcript import Transcript, TranscriptSegment
from src.domain.repositories.call_recording_repository import CallRecordingRepository
from src.domain.repositories.intent_extraction_repository import IntentExtractionRepository
from src.domain.repositories.review_queue_repository import ReviewQueueRepository
from src.domain.repositories.transcript_repository import TranscriptRepository
from src.domain.services.intent_validator import IntentValidator
from src.domain.services.language_detector import detect_language
from src.infrastructure.audio.ffmpeg_preprocessor import FFmpegPreprocessor
from src.infrastructure.prompts.prompt_registry import PromptRegistry
from src.ports.llm_provider import LLMProvider
from src.ports.storage_provider import StorageProvider
from src.ports.stt_provider import SpeechToTextProvider


@dataclass
class ExtractionResult:
    extraction: IntentExtraction
    requires_review: bool


class CallProcessingOrchestrator:
    """Orchestrates call audio download, STT, intent extraction, and HITL routing."""

    def __init__(
        self,
        call_repo: CallRecordingRepository,
        transcript_repo: TranscriptRepository,
        intent_repo: IntentExtractionRepository,
        review_repo: ReviewQueueRepository,
        storage: StorageProvider,
        stt: SpeechToTextProvider,
        llm: LLMProvider,
        prompt_registry: PromptRegistry,
        intent_validator: IntentValidator,
        confidence_router: ConfidenceRouter,
        preprocessor: FFmpegPreprocessor | None = None,
    ) -> None:
        self._call_repo = call_repo
        self._transcript_repo = transcript_repo
        self._intent_repo = intent_repo
        self._review_repo = review_repo
        self._storage = storage
        self._stt = stt
        self._llm = llm
        self._prompt_registry = prompt_registry
        self._intent_validator = intent_validator
        self._confidence_router = confidence_router
        self._preprocessor = preprocessor or FFmpegPreprocessor()

    async def process_call(
        self,
        call_id: UUID,
        *,
        prompt_version: str | None = None,
    ) -> tuple[Transcript, IntentExtraction, ReviewQueueItem | None]:
        recording = await self._call_repo.get_by_id(call_id)
        if recording is None:
            raise ValueError(f"Call recording not found: {call_id}")

        recording.mark_processing()
        await self._call_repo.update(recording)

        try:
            transcript = await self._run_stt(call_id, recording)
            recording.mark_transcribed()
            await self._call_repo.update(recording)

            recording.mark_extracting()
            await self._call_repo.update(recording)

            extraction_result = await self._run_extraction(
                call_id,
                transcript,
                prompt_version=prompt_version,
            )
            extraction = extraction_result.extraction

            existing = await self._intent_repo.get_by_call_id(call_id)
            if existing:
                extraction.id = existing.id
                extraction = await self._intent_repo.update(extraction)
            else:
                extraction = await self._intent_repo.create(extraction)

            review_item: ReviewQueueItem | None = None
            if extraction_result.requires_review:
                recording.mark_review_required()
                review_item = await self._review_repo.create(
                    ReviewQueueItem(extraction_id=extraction.id)
                )
            else:
                recording.mark_completed()

            await self._call_repo.update(recording)
            return transcript, extraction, review_item

        except Exception:
            recording.mark_failed()
            await self._call_repo.update(recording)
            raise

    async def process_stt(self, call_id: UUID) -> Transcript:
        """STT-only path for backward compatibility in tests."""
        recording = await self._call_repo.get_by_id(call_id)
        if recording is None:
            raise ValueError(f"Call recording not found: {call_id}")

        recording.mark_processing()
        await self._call_repo.update(recording)

        try:
            transcript = await self._run_stt(call_id, recording)
            recording.mark_transcribed()
            await self._call_repo.update(recording)
            return transcript
        except Exception:
            recording.mark_failed()
            await self._call_repo.update(recording)
            raise

    async def _run_stt(self, call_id: UUID, recording) -> Transcript:
        audio_bytes = await self._storage.download(recording.storage_key)
        suffix = Path(recording.storage_key).suffix or ".wav"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_path = tmp / f"input{suffix}"
            output_path = tmp / "normalized.wav"
            input_path.write_bytes(audio_bytes)

            metadata = self._preprocessor.normalize(input_path, output_path)
            stt_result = await self._stt.transcribe(output_path)

        detected = detect_language(
            stt_result.full_text,
            provider_hint=stt_result.detected_language,
        )
        recording.detected_language = detected
        recording.duration_sec = metadata.duration_sec

        segments = [
            TranscriptSegment(
                start=seg.get("start", 0.0),
                end=seg.get("end", 0.0),
                text=seg.get("text", ""),
                confidence=seg.get("confidence"),
            )
            for seg in stt_result.segments
        ]

        existing = await self._transcript_repo.get_by_call_id(call_id)
        if existing:
            existing.full_text = stt_result.full_text
            existing.segments = segments
            existing.stt_provider = stt_result.provider
            existing.stt_model = stt_result.model
            return await self._transcript_repo.update(existing)

        transcript = Transcript(
            call_id=call_id,
            full_text=stt_result.full_text,
            segments=segments,
            stt_provider=stt_result.provider,
            stt_model=stt_result.model,
        )
        return await self._transcript_repo.create(transcript)

    async def _run_extraction(
        self,
        call_id: UUID,
        transcript: Transcript,
        *,
        prompt_version: str | None = None,
    ) -> ExtractionResult:
        bundle = self._prompt_registry.load(prompt_version)
        llm_result = await self._llm.extract_structured(
            transcript.full_text,
            bundle.schema,
            prompt_version=bundle.version,
        )

        validated = self._intent_validator.validate(llm_result.data)
        routing = self._confidence_router.route(llm_result.confidence, validated)

        raw_output = dict(llm_result.raw_output or llm_result.data)
        raw_output["confidence_signals"] = routing.signals.signals
        raw_output["validation_notes"] = validated.validation_notes

        extraction = IntentExtraction(
            call_id=call_id,
            side=validated.side,
            stock_symbol=validated.stock_symbol,
            quantity=validated.quantity,
            price=validated.price,
            exchange=validated.exchange,
            confidence=routing.final_confidence,
            prompt_version=bundle.version,
            llm_provider=llm_result.provider,
            raw_llm_output=raw_output,
        )
        return ExtractionResult(extraction=extraction, requires_review=routing.requires_review)
