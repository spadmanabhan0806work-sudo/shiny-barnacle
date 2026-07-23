
from src.domain.services.stock_symbol_resolver import StockSymbolResolver


class TestStockSymbolResolver:
    def test_resolve_known_symbol(self, tmp_path):
        csv = tmp_path / "symbols.csv"
        csv.write_text("RELIANCE,RELIANCE INDUSTRIES,NSE\nTCS,TATA CONSULTANCY SERVICES,NSE\n")
        resolver = StockSymbolResolver(csv)
        assert resolver.resolve("RELIANCE") == "RELIANCE"
        assert resolver.resolve("reliance") == "RELIANCE"

    def test_resolve_by_name(self, tmp_path):
        csv = tmp_path / "symbols.csv"
        csv.write_text("RELIANCE,RELIANCE INDUSTRIES,NSE\n")
        resolver = StockSymbolResolver(csv)
        assert resolver.resolve("RELIANCE INDUSTRIES") == "RELIANCE"

    def test_resolve_unknown_returns_none(self, tmp_path):
        csv = tmp_path / "symbols.csv"
        csv.write_text("RELIANCE,RELIANCE INDUSTRIES,NSE\n")
        resolver = StockSymbolResolver(csv)
        assert resolver.resolve("UNKNOWN_STOCK") is None

    def test_missing_file_returns_empty(self, tmp_path):
        resolver = StockSymbolResolver(tmp_path / "missing.csv")
        assert resolver.symbol_count == 0
