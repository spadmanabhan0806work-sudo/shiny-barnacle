from src.domain.services.language_detector import detect_language


class TestLanguageDetector:
    def test_english_text(self):
        assert detect_language("Buy one hundred shares of Reliance") == "en"

    def test_hindi_text(self):
        assert detect_language("मुझे सौ शेयर खरीदने हैं") == "hi"

    def test_malayalam_text(self):
        assert detect_language("എനിക്ക് ഷെയറുകൾ വാങ്ങണം") == "ml"

    def test_gujarati_text(self):
        assert detect_language("મને શેર ખરીદવા છે") == "gu"

    def test_mixed_hinglish(self):
        assert detect_language("Mujhe Reliance ke shares buy karne hain") == "mixed"

    def test_provider_hint_en(self):
        assert detect_language("", provider_hint="en-IN") == "en"

    def test_empty_text_unknown(self):
        assert detect_language("") == "unknown"
