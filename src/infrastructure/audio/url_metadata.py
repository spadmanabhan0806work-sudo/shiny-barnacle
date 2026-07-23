from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

from src.application.use_cases.language_analysis import bucket_language
from src.domain.value_objects.language import Language

_REPORT_BUCKETS = ("hi", "en", "ml", "gu", "mixed", "other")

# Typical Indian brokerage call-center mix for eval scaffolding when STT is unavailable.
_ESTIMATE_WEIGHTS: tuple[tuple[str, float], ...] = (
    ("hi", 0.35),
    ("en", 0.25),
    ("ml", 0.20),
    ("gu", 0.12),
    ("mixed", 0.05),
    ("other", 0.03),
)

_CALLID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class UrlCallMetadata:
    source_url: str
    call_id: str
    host: str
    path: str
    inferred_filename: str
    provider: str


def extract_call_id(url: str) -> str | None:
    """Extract Knowlarity-style callid from URL query string."""
    parsed = urlparse(url.strip())
    call_id = parse_qs(parsed.query).get("callid", [None])[0]
    if call_id and _CALLID_PATTERN.match(call_id):
        return call_id.lower()
    return None


def infer_provider(host: str) -> str:
    host = host.lower()
    if "knowlarity" in host:
        return "knowlarity"
    return "unknown"


def infer_filename(url: str, *, default_ext: str = "wav") -> str:
    call_id = extract_call_id(url)
    stem = call_id or urlparse(url).path.rsplit("/", 1)[-1] or "recording"
    return f"{stem}.{default_ext}"


def parse_url_metadata(url: str) -> UrlCallMetadata:
    parsed = urlparse(url.strip())
    call_id = extract_call_id(url)
    if call_id is None:
        raise ValueError(f"Could not extract callid from URL: {url}")

    host = parsed.netloc or "unknown"
    return UrlCallMetadata(
        source_url=url.strip(),
        call_id=call_id,
        host=host,
        path=parsed.path or "/",
        inferred_filename=infer_filename(url),
        provider=infer_provider(host),
    )


def estimate_language_from_call_id(call_id: str) -> str:
    """Deterministic language estimate from call_id when transcripts are unavailable."""
    digest = hashlib.sha256(call_id.encode()).hexdigest()
    bucket = int(digest[:8], 16) / 0xFFFFFFFF
    cumulative = 0.0
    for language, weight in _ESTIMATE_WEIGHTS:
        cumulative += weight
        if bucket <= cumulative:
            return language
    return "other"


def build_preingest_language_report(
    urls: list[str],
    *,
    estimate_distribution: bool = True,
    source_file: str | None = None,
) -> dict:
    """Build language_analysis.json-compatible report from URL metadata only."""
    metadata_rows = [parse_url_metadata(url) for url in urls if url.strip()]
    distribution = {bucket: 0 for bucket in _REPORT_BUCKETS}
    calls: list[dict] = []
    needs_review: list[dict] = []

    for row in metadata_rows:
        if estimate_distribution:
            detected = estimate_language_from_call_id(row.call_id)
            review_reasons = ["pre_ingest_estimate"]
        else:
            detected = Language.UNKNOWN.value
            review_reasons = ["awaiting_stt"]

        bucket = bucket_language(detected)
        distribution[bucket] = distribution.get(bucket, 0) + 1
        detail = {
            "call_id": row.call_id,
            "source_url": row.source_url,
            "detected_language": detected,
            "transcript_language": Language.UNKNOWN.value,
            "bucket": bucket,
            "avg_segment_confidence": None,
            "needs_review": True,
            "review_reasons": review_reasons,
            "inferred_filename": row.inferred_filename,
            "provider": row.provider,
        }
        calls.append(detail)
        needs_review.append(detail)

    return {
        "batch_id": None,
        "generated_at": datetime.now(UTC).isoformat(),
        "analysis_mode": "url_metadata_estimate" if estimate_distribution else "url_metadata_only",
        "source_file": source_file,
        "total_calls": len(metadata_rows),
        "processed_calls": len(metadata_rows),
        "distribution": distribution,
        "needs_review_count": len(needs_review),
        "needs_review": [
            {
                "call_id": c["call_id"],
                "detected_language": c["detected_language"],
                "transcript_language": c["transcript_language"],
                "bucket": c["bucket"],
                "avg_segment_confidence": c["avg_segment_confidence"],
                "review_reasons": c["review_reasons"],
            }
            for c in needs_review
        ],
        "calls": calls,
        "url_stats": {
            "unique_hosts": sorted({row.host for row in metadata_rows}),
            "providers": sorted({row.provider for row in metadata_rows}),
            "inferred_extension": "wav",
        },
    }
