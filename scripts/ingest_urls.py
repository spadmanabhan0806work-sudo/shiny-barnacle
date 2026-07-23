#!/usr/bin/env python3
"""Submit recording URLs from a text file to Operyx AI for batch ingestion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

from src.infrastructure.audio.url_metadata import build_preingest_language_report

MAX_URLS_PER_BATCH = 100


def read_urls(path: Path) -> list[str]:
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "," in line and not line.startswith("http"):
            line = line.split(",", 1)[0].strip()
        if line.startswith("http"):
            urls.append(line)
    return urls


def chunk_urls(urls: list[str], size: int = MAX_URLS_PER_BATCH) -> list[list[str]]:
    return [urls[i : i + size] for i in range(0, len(urls), size)]


def url_file_stats(urls: list[str]) -> dict:
    hosts = sorted({u.split("/")[2] for u in urls if "://" in u})
    return {
        "url_count": len(urls),
        "unique_urls": len(set(urls)),
        "hosts": hosts,
        "batch_count": len(chunk_urls(urls)),
    }


def write_language_preview(urls: list[str], output: Path, source_file: Path) -> dict:
    report = build_preingest_language_report(
        urls,
        estimate_distribution=True,
        source_file=str(source_file.resolve()),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def submit_batch(client: httpx.Client, api_base: str, urls: list[str]) -> dict:
    response = client.post(
        f"{api_base.rstrip('/')}/api/v1/calls/batch/from-urls",
        json={"urls": urls},
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Ingest failed ({response.status_code}): {response.text}")
    return response.json()


def api_available(api_base: str, timeout_sec: float = 3.0) -> bool:
    try:
        response = httpx.get(f"{api_base.rstrip('/')}/api/v1/health", timeout=timeout_sec)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch-ingest call recording URLs")
    parser.add_argument(
        "url_file",
        nargs="?",
        default=r"c:\Users\natar\Downloads\recording_urls.txt",
        help="Path to text file with one URL per line",
    )
    parser.add_argument(
        "--api-base",
        default="http://localhost:8000",
        help="Operyx API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--output",
        default="eval/reports/ingest_batch.json",
        help="Where to write batch metadata JSON",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="After ingest, run language analysis on the first batch (requires DB)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse URLs and print stats without calling the API",
    )
    parser.add_argument(
        "--generate-preview",
        metavar="PATH",
        nargs="?",
        const="eval/reports/language_analysis.json",
        help="Write pre-ingest language_analysis.json from URL metadata (no API/DB)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Ingest only the first N URLs (smoke test)",
    )
    args = parser.parse_args()

    url_path = Path(args.url_file)
    if not url_path.exists():
        print(f"URL file not found: {url_path}", file=sys.stderr)
        return 1

    urls = read_urls(url_path)
    if args.limit is not None:
        urls = urls[: args.limit]
    if not urls:
        print(f"No URLs found in {url_path}", file=sys.stderr)
        return 1

    stats = url_file_stats(urls)
    print(
        f"URL file: {url_path} — {stats['url_count']} URLs "
        f"({stats['unique_urls']} unique) across {stats['batch_count']} batch(es)"
    )
    print(f"Hosts: {', '.join(stats['hosts'])}")

    if args.generate_preview is not None:
        preview_path = Path(args.generate_preview)
        report = write_language_preview(urls, preview_path, url_path)
        print(f"Pre-ingest language preview written to {preview_path}")
        print("Distribution (estimate):", report["distribution"])
        if args.dry_run:
            return 0

    if args.dry_run:
        return 0

    if not api_available(args.api_base):
        print(
            f"API not reachable at {args.api_base}; writing pre-ingest language preview only.",
            file=sys.stderr,
        )
        preview_path = Path("eval/reports/language_analysis.json")
        report = write_language_preview(urls, preview_path, url_path)
        print(f"Pre-ingest language preview written to {preview_path}")
        print("Distribution (estimate):", report["distribution"])
        return 0

    chunks = chunk_urls(urls)
    print(
        f"Submitting {len(urls)} URLs in {len(chunks)} batch(es) "
        f"to {args.api_base}/api/v1/calls/batch/from-urls"
    )

    batches: list[dict] = []
    all_errors: list[str] = []

    with httpx.Client(timeout=300.0) as client:
        for index, chunk in enumerate(chunks, start=1):
            print(f"  Batch {index}/{len(chunks)}: {len(chunk)} URLs...")
            payload = submit_batch(client, args.api_base, chunk)
            batches.append(
                {
                    "batch_id": payload["batch_id"],
                    "total": payload["total"],
                    "errors": payload.get("errors", []),
                    "url_count": len(chunk),
                }
            )
            all_errors.extend(payload.get("errors", []))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "batch_ids": [b["batch_id"] for b in batches],
        "batches": batches,
        "total_calls_ingested": sum(b["total"] for b in batches),
        "errors": all_errors,
        "source_file": str(url_path.resolve()),
        "url_count_submitted": len(urls),
    }
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    primary_batch_id = batches[0]["batch_id"]
    print(f"Primary batch: {primary_batch_id}")
    print(f"All batch IDs: {', '.join(summary['batch_ids'])}")
    print(f"Calls ingested: {summary['total_calls_ingested']}")
    if all_errors:
        print(f"Errors: {len(all_errors)} (see {output_path})")
    print(f"Metadata saved to {output_path}")
    print(f"Export results: GET {args.api_base}/api/v1/exports/{primary_batch_id}")

    if args.analyze:
        from scripts.analyze_languages import main as analyze_main

        sys.argv = [
            "analyze_languages.py",
            "--ingest-metadata",
            str(output_path),
            "--output",
            "eval/reports/language_analysis.json",
        ]
        return analyze_main()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
