import pytest

from src.domain.services.numeric_parser import NumericParser


class TestNumericParser:
  @pytest.fixture
  def parser(self):
    return NumericParser()

  def test_parse_digits(self, parser):
    assert parser.parse_int("100") == 100
    assert parser.parse_int("1,000") == 1000

  def test_parse_english_words(self, parser):
    assert parser.parse_int("one hundred") == 100
    assert parser.parse_int("fifty") == 50

  def test_parse_hindi_words(self, parser):
    assert parser.parse_int("पचास") == 50
    assert parser.parse_int("सौ") == 100

  def test_parse_malayalam_words(self, parser):
    assert parser.parse_int("നൂറ്") == 100

  def test_parse_lakhs_crores(self, parser):
    assert parser.parse_int("one lakh") == 100_000
    assert parser.parse_int("two crore") == 20_000_000

  def test_parse_romanized_hindi(self, parser):
    assert parser.parse_int("sau") == 100
    assert parser.parse_int("pachas") == 50

  def test_parse_decimal(self, parser):
    assert parser.parse_decimal("2500.50") == pytest.approx(2500.50)

  def test_invalid_returns_none(self, parser):
    assert parser.parse_int("not-a-number") is None
