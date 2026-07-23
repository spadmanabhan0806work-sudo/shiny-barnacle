from __future__ import annotations

import pytest

from eval.metrics.core import accuracy, f1_score, precision, recall
from eval.metrics.field_scorers import field_match, score_all_fields, score_field


class TestCoreMetrics:
    def test_accuracy(self):
        assert accuracy(8, 10) == 0.8
        assert accuracy(0, 0) == 0.0

    def test_precision_recall_f1(self):
        prec = precision(8, 2)
        rec = recall(8, 2)
        assert prec == 0.8
        assert rec == 0.8
        assert f1_score(prec, rec) == pytest.approx(0.8)


class TestFieldScorers:
    def test_side_exact_match(self):
        assert field_match("side", "BUY", "buy") is True
        assert field_match("side", "BUY", "SELL") is False

    def test_stock_fuzzy_match(self):
        assert field_match("stock_symbol", "RELIANCE", "RELIANCE") is True
        assert field_match("stock_symbol", "RELIANCE", "RELIANCEE") is True
        assert field_match("stock_symbol", "RELIANCE", "TCS") is False

    def test_quantity_and_price(self):
        assert field_match("quantity", 100, 100) is True
        assert field_match("quantity", 100, 101) is False
        assert field_match("price", 2500.0, 2500.0) is True
        assert field_match("price", 2500.0, 2500.01) is True

    def test_score_all_fields(self):
        pairs = [
            (
                {
                    "side": "BUY",
                    "stock_symbol": "RELIANCE",
                    "quantity": 100,
                    "price": 2500.0,
                    "exchange": "NSE",
                },
                {
                    "side": "BUY",
                    "stock_symbol": "RELIANCE",
                    "quantity": 100,
                    "price": 2500.0,
                    "exchange": "NSE",
                },
            ),
            (
                {
                    "side": "SELL",
                    "stock_symbol": "TCS",
                    "quantity": 50,
                    "price": 3800.0,
                    "exchange": "NSE",
                },
                {
                    "side": "BUY",
                    "stock_symbol": "TCS",
                    "quantity": 50,
                    "price": 3800.0,
                    "exchange": "NSE",
                },
            ),
        ]
        metrics = score_all_fields(pairs)
        assert metrics["side"].accuracy == 0.5
        assert metrics["stock_symbol"].accuracy == 1.0
        assert score_field("exchange", pairs).accuracy == 1.0
