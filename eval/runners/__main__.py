"""CLI entry point: python -m eval.runners --dataset eval/datasets/sample_gold.json"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from eval.runners.benchmark_runner import BenchmarkRunner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Operyx benchmark against a gold dataset")
    parser.add_argument(
        "--dataset",
        required=True,
        type=Path,
        help="Path to gold dataset JSON",
    )
    parser.add_argument("--prompt-version", default="v1.0.0")
    parser.add_argument("--stt-provider", default="mock")
    parser.add_argument("--llm-provider", default="mock")
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=Path("eval/reports/output"),
        help="Directory for HTML report output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print metrics JSON to stdout",
    )
    args = parser.parse_args(argv)

    if not args.dataset.exists():
        print(f"Dataset not found: {args.dataset}", file=sys.stderr)
        return 1

    runner = BenchmarkRunner(reports_dir=args.reports_dir)
    result = runner.run_from_dataset(
        args.dataset,
        prompt_version=args.prompt_version,
        stt_provider=args.stt_provider,
        llm_provider=args.llm_provider,
    )

    report_path = args.reports_dir / f"{result.run_id}.html"
    print(f"Run ID: {result.run_id}")
    print(f"Macro accuracy: {result.summary['macro_accuracy']:.1%}")
    print(f"HTML report: {report_path}")

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
