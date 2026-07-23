from __future__ import annotations

import pytest

from src.infrastructure.audio.url_metadata import (
    build_preingest_language_report,
    estimate_language_from_call_id,
    extract_call_id,
    infer_filename,
    parse_url_metadata,
)


SAMPLE_URL = (
    "https://sr.knowlarity.com/vr/fetchsound/"
    "?callid=75193f3c-2606-4984-9f34-888c3bf843b7"
)


def test_extract_call_id_from_knowlarity_url():
    assert extract_call_id(SAMPLE_URL) == "75193f3c-2606-4984-9f34-888c3bf843b7"


def test_infer_filename_uses_callid():
    assert infer_filename(SAMPLE_URL) == "75193f3c-2606-4984-9f34-888c3bf843b7.wav"


def test_parse_url_metadata():
    meta = parse_url_metadata(SAMPLE_URL)
    assert meta.provider == "knowlarity"
    assert meta.host == "sr.knowlarity.com"
    assert meta.inferred_filename.endswith(".wav")


def test_estimate_language_is_deterministic():
    call_id = "75193f3c-2606-4984-9f34-888c3bf843b7"
    assert estimate_language_from_call_id(call_id) == estimate_language_from_call_id(call_id)


def test_build_preingest_language_report_counts_urls():
    urls = [SAMPLE_URL, SAMPLE_URL.replace("75193", "75293")]
    report = build_preingest_language_report(urls, source_file="recording_urls.txt")
    assert report["total_calls"] == 2
    assert report["analysis_mode"] == "url_metadata_estimate"
    assert sum(report["distribution"].values()) == 2


def test_build_preingest_language_report_unknown_mode():
    report = build_preingest_language_report([SAMPLE_URL], estimate_distribution=False)
    assert report["distribution"]["other"] == 1
    assert report["calls"][0]["review_reasons"] == ["awaiting_stt"]


def test_parse_url_metadata_rejects_missing_callid():
    with pytest.raises(ValueError, match="Could not extract callid"):
        parse_url_metadata("https://example.com/audio.wav")
