from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    TypeDecorator,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class GUID(TypeDecorator):
    """Platform-independent UUID type."""

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class Base(DeclarativeBase):
    pass


class CallRecordingModel(Base):
    __tablename__ = "call_recordings"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    detected_language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    transcript: Mapped["TranscriptModel | None"] = relationship(back_populates="call_recording")
    intent_extractions: Mapped[list["IntentExtractionModel"]] = relationship(
        back_populates="call_recording"
    )
    annotations: Mapped[list["AnnotationModel"]] = relationship(back_populates="call_recording")


class TranscriptModel(Base):
    __tablename__ = "transcripts"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    call_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("call_recordings.id"), unique=True, nullable=False
    )
    full_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    segments: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    stt_provider: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    stt_model: Mapped[str] = mapped_column(String(128), nullable=False, default="")

    call_recording: Mapped["CallRecordingModel"] = relationship(back_populates="transcript")


class IntentExtractionModel(Base):
    __tablename__ = "intent_extractions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    call_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("call_recordings.id"), nullable=False, index=True
    )
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    stock_symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    exchange: Mapped[str] = mapped_column(String(8), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    llm_provider: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    raw_llm_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    call_recording: Mapped["CallRecordingModel"] = relationship(back_populates="intent_extractions")
    review_items: Mapped[list["ReviewQueueItemModel"]] = relationship(
        back_populates="extraction"
    )


class AnnotationModel(Base):
    __tablename__ = "annotations"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    call_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("call_recordings.id"), nullable=False, index=True
    )
    annotator_id: Mapped[str] = mapped_column(String(128), nullable=False)
    ground_truth: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")

    call_recording: Mapped["CallRecordingModel"] = relationship(back_populates="annotations")


class ReviewQueueItemModel(Base):
    __tablename__ = "review_queue_items"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    extraction_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("intent_extractions.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    corrected_fields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    reviewer_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    extraction: Mapped["IntentExtractionModel"] = relationship(back_populates="review_items")


class PromptVersionModel(Base):
    __tablename__ = "prompt_versions"

    version: Mapped[str] = mapped_column(String(32), primary_key=True)
    module: Mapped[str] = mapped_column(String(64), nullable=False, default="call_to_trade")
    system_prompt_hash: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ab_weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)


class EvaluationRunModel(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    stt_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    llm_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ran_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class BatchUploadModel(Base):
    __tablename__ = "batch_uploads"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    call_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class BatchModel(Base):
    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    call_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    changes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
