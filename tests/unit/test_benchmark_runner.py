from __future__ import annotations

from pathlib import Path

import pytest

from eval.runners.benchmark_runner import BenchmarkPair, BenchmarkRunner


@pytest.fixture
def sample_dataset_path() -> Path:
    return Path("eval/datasets/sample_gold.json")


class TestBenchmarkRunner:
    def test_run_from_dataset(self, sample_dataset_path, tmp_path):
        runner = BenchmarkRunner(reports_dir=tmp_path / "reports")
        result = runner.run_from_dataset(
            sample_dataset_path,
            prompt_version="v1.0.0",
            stt_provider="mock",
            llm_provider="mock",
        )

        assert result.summary["total"] == 4
        assert result.summary["matched_all_fields"] == 2
        assert result.field_metrics["side"].accuracy == 0.75
        assert result.field_metrics["stock_symbol"].accuracy == 0.75
        assert (tmp_path / "reports" / f"{result.run_id}.html").exists()

    def test_run_from_pairs(self, tmp_path):
        runner = BenchmarkRunner(reports_dir=tmp_path / "reports")
        pairs = [
            BenchmarkPair(
                call_id=None,
                ground_truth={
                    "side": "BUY",
                    "stock_symbol": "RELIANCE",
                    "quantity": 100,
                    "price": 2500.0,
                    "exchange": "NSE",
                },
                prediction={
                    "side": "BUY",
                    "stock_symbol": "RELIANCE",
                    "quantity": 100,
                    "price": 2500.0,
                    "exchange": "NSE",
                },
            )
        ]
        result = runner.run_from_pairs(
            pairs,
            dataset_name="unit_test",
            prompt_version="v1.0.0",
            stt_provider="mock",
            llm_provider="mock",
        )
        assert result.summary["matched_all_fields"] == 1
        assert result.field_metrics["side"].f1 == 1.0

    def test_cli_main(self, sample_dataset_path, tmp_path, capsys):
        from eval.runners.__main__ import main

        exit_code = main(
            [
                "--dataset",
                str(sample_dataset_path),
                "--reports-dir",
                str(tmp_path / "reports"),
                "--json",
            ]
        )
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Macro accuracy" in captured.out
        assert '"aggregate_metrics"' in captured.out
