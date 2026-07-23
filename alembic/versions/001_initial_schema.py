"""Initial schema for Operyx AI core tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "call_recordings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        sa.Column("storage_key", sa.String(512), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("detected_language", sa.String(16), nullable=True),
        sa.Column("duration_sec", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "transcripts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "call_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("call_recordings.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column("full_text", sa.Text, nullable=False, server_default=""),
        sa.Column("segments", postgresql.JSONB, nullable=True),
        sa.Column("stt_provider", sa.String(64), nullable=False, server_default=""),
        sa.Column("stt_model", sa.String(128), nullable=False, server_default=""),
    )

    op.create_table(
        "intent_extractions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "call_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("call_recordings.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("side", sa.String(8), nullable=False),
        sa.Column("stock_symbol", sa.String(32), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("exchange", sa.String(8), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("prompt_version", sa.String(32), nullable=False, server_default=""),
        sa.Column("llm_provider", sa.String(64), nullable=False, server_default=""),
        sa.Column("raw_llm_output", postgresql.JSONB, nullable=True),
    )

    op.create_table(
        "annotations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "call_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("call_recordings.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("annotator_id", sa.String(128), nullable=False),
        sa.Column("ground_truth", postgresql.JSONB, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
    )

    op.create_table(
        "review_queue_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "extraction_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("intent_extractions.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("corrected_fields", postgresql.JSONB, nullable=True),
        sa.Column("reviewer_id", sa.String(128), nullable=True),
    )

    op.create_table(
        "prompt_versions",
        sa.Column("version", sa.String(32), primary_key=True),
        sa.Column("module", sa.String(64), nullable=False, server_default="call_to_trade"),
        sa.Column("system_prompt_hash", sa.Text, nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("ab_weight", sa.Float, nullable=False, server_default="1.0"),
    )

    op.create_table(
        "evaluation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prompt_version", sa.String(32), nullable=False),
        sa.Column("stt_provider", sa.String(64), nullable=False),
        sa.Column("llm_provider", sa.String(64), nullable=False),
        sa.Column("aggregate_metrics", postgresql.JSONB, nullable=True),
        sa.Column(
            "ran_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("evaluation_runs")
    op.drop_table("prompt_versions")
    op.drop_table("review_queue_items")
    op.drop_table("annotations")
    op.drop_table("intent_extractions")
    op.drop_table("transcripts")
    op.drop_table("call_recordings")
