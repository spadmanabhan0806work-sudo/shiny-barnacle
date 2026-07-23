#!/usr/bin/env python3
"""Generate language distribution report for a batch or set of calls."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID

from src.application.use_cases.language_analysis import write_language_report
from src.infrastructure.persistence.database import get_session_factory


async def _resolve_call_ids_from_batches(session, batch_ids: list[UUID]) -> list[UUID]:
    from sqlalchemy import select

    from src.infrastructure.persistence.models import BatchUploadModel

    call_ids: list[UUID] = []
    for batch_id in batch_ids:
        result = await session.execute(
            select(BatchUploadModel).where(BatchUploadModel.id == batch_id)
        )
        batch = result.scalar_one_or_none()
        if batch is None:
            raise ValueError(f"Batch not found: {batch_id}")
        call_ids.extend(UUID(str(cid)) for cid in batch.call_ids)
    return call_ids


async def _run(
    batch_id: UUID | None,
    output: Path,
    *,
    ingest_metadata: Path | None = None,
) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            call_ids = None
            if ingest_metadata is not None:
                import json

                meta = json.loads(ingest_metadata.read_text(encoding="utf-8"))
                batch_ids = [UUID(bid) for bid in meta.get("batch_ids", [])]
                if not batch_ids and meta.get("batch_id"):
                    batch_ids = [UUID(meta["batch_id"])]
                if not batch_ids:
                    raise ValueError("No batch_ids in ingest metadata")
                call_ids = await _resolve_call_ids_from_batches(session, batch_ids)
                batch_id = batch_ids[0] if len(batch_ids) == 1 else None

            report = await write_language_report(
                session,
                output,
                batch_id=batch_id,
                call_ids=call_ids,
            )
            await session.commit()
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    print(f"Language report written to {output}")
    print("Distribution:", report.distribution)
    print(f"Needs review: {len(report.needs_review)} / {report.processed_calls}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze call language distribution")
    parser.add_argument("--batch-id", help="Batch UUID from ingest_urls.py")
    parser.add_argument(
        "--ingest-metadata",
        default=None,
        help="Path to ingest_batch.json (analyzes all batches listed)",
    )
    parser.add_argument(
        "--output",
        default="eval/reports/language_analysis.json",
        help="Output JSON report path",
    )
    args = parser.parse_args()

    if not args.batch_id and not args.ingest_metadata:
        parser.error("Provide --batch-id or --ingest-metadata")

    batch_id = None
    ingest_metadata = Path(args.ingest_metadata) if args.ingest_metadata else None
    if args.batch_id:
        try:
            batch_id = UUID(args.batch_id)
        except ValueError:
            print(f"Invalid batch id: {args.batch_id}", file=sys.stderr)
            return 1

    return asyncio.run(_run(batch_id, Path(args.output), ingest_metadata=ingest_metadata))


if __name__ == "__main__":
    raise SystemExit(main())
