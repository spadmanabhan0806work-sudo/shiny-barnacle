import pytest

from src.domain.services.intent_validator import IntentValidator
from src.domain.services.numeric_parser import NumericParser
from src.domain.services.stock_symbol_resolver import StockSymbolResolver


class TestIntentValidator:
  @pytest.fixture
  def validator(self, tmp_path):
    csv = tmp_path / "symbols.csv"
    csv.write_text("RELIANCE,RELIANCE INDUSTRIES,NSE\nTCS,TATA CONSULTANCY SERVICES,NSE\n")
    resolver = StockSymbolResolver(csv)
    return IntentValidator(resolver, NumericParser())

  def test_validates_and_normalizes(self, validator):
    result = validator.validate(
      {
        "side": "buy",
        "stock_symbol": "Reliance",
        "quantity": "one hundred",
        "price": "2500",
        "exchange": "nse",
      }
    )
    assert result.side == "BUY"
    assert result.stock_symbol == "RELIANCE"
    assert result.quantity == 100
    assert result.price == 2500.0
    assert result.exchange == "NSE"

  def test_invalid_side_defaults_with_note(self, validator):
    result = validator.validate(
      {
        "side": "HOLD",
        "stock_symbol": "RELIANCE",
        "quantity": 10,
        "price": 100,
        "exchange": "NSE",
      }
    )
    assert result.side == "BUY"
    assert "invalid_side" in result.validation_notes

  def test_unknown_stock(self, validator):
    result = validator.validate(
      {
        "side": "BUY",
        "stock_symbol": "UNKNOWNCO",
        "quantity": 10,
        "price": 100,
        "exchange": "NSE",
      }
    )
    assert result.stock_symbol == "UNKNOWNCO"
    assert "unknown_stock" in result.validation_notes
