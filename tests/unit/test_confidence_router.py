from src.application.services.confidence_router import ConfidenceRouter
from src.domain.services.intent_validator import ValidatedIntent


class TestConfidenceRouter:
  def test_high_confidence_passes(self):
    router = ConfidenceRouter(threshold=0.85)
    validated = ValidatedIntent(
      side="BUY",
      stock_symbol="RELIANCE",
      quantity=100,
      price=2500.0,
      exchange="NSE",
      validation_notes=[],
      stock_match_confidence=1.0,
    )
    decision = router.route(0.95, validated)
    assert decision.requires_review is False
    assert decision.final_confidence >= 0.85

  def test_low_confidence_routes_to_review(self):
    router = ConfidenceRouter(threshold=0.85)
    validated = ValidatedIntent(
      side="BUY",
      stock_symbol="UNKNOWN",
      quantity=1,
      price=0.0,
      exchange="NSE",
      validation_notes=["unknown_stock", "invalid_price"],
      stock_match_confidence=0.0,
    )
    decision = router.route(0.5, validated)
    assert decision.requires_review is True
    assert decision.final_confidence < 0.85

  def test_signals_exposed(self):
    router = ConfidenceRouter()
    validated = ValidatedIntent(
      side="BUY",
      stock_symbol="RELIANCE",
      quantity=100,
      price=2500.0,
      exchange="NSE",
      validation_notes=[],
      stock_match_confidence=1.0,
    )
    decision = router.route(0.9, validated)
    assert "llm" in decision.signals.signals
    assert "final" in decision.signals.signals
