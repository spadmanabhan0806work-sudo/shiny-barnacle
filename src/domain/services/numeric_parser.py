from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


class NumericParser:
    """Parse spoken numbers in English, Hindi, and Malayalam to int/decimal."""

    _ENGLISH_WORDS: dict[str, int] = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
        "twenty": 20,
        "thirty": 30,
        "forty": 40,
        "fifty": 50,
        "sixty": 60,
        "seventy": 70,
        "eighty": 80,
        "ninety": 90,
        "hundred": 100,
        "thousand": 1000,
        "lakh": 100_000,
        "lakhs": 100_000,
        "lac": 100_000,
        "lacs": 100_000,
        "crore": 10_000_000,
        "crores": 10_000_000,
    }

    _HINDI_WORDS: dict[str, int] = {
        "शून्य": 0,
        "एक": 1,
        "दो": 2,
        "तीन": 3,
        "चार": 4,
        "पांच": 5,
        "पाँच": 5,
        "छह": 6,
        "सात": 7,
        "आठ": 8,
        "नौ": 9,
        "दस": 10,
        "बीस": 20,
        "तीस": 30,
        "चालीस": 40,
        "पचास": 50,
        "साठ": 60,
        "सत्तर": 70,
        "अस्सी": 80,
        "नब्बे": 90,
        "सौ": 100,
        "हजार": 1000,
        "हज़ार": 1000,
        "लाख": 100_000,
        "करोड़": 10_000_000,
    }

    _MALAYALAM_WORDS: dict[str, int] = {
        "പൂജ്യം": 0,
        "ഒന്ന്": 1,
        "രണ്ട്": 2,
        "മൂന്ന്": 3,
        "നാല്": 4,
        "അഞ്ച്": 5,
        "ആറ്": 6,
        "ഏഴ്": 7,
        "എട്ട്": 8,
        "ഒമ്പത്": 9,
        "പത്ത്": 10,
        "ഇരുപത്": 20,
        "മുപ്പത്": 30,
        "നാല്പ്പത്": 40,
        "അമ്പത്": 50,
        "അറുപത്": 60,
        "എഴുപത്": 70,
        "എൺപത്": 80,
        "തൊണ്ണൂറ്": 90,
        "നൂറ്": 100,
        "ആയിരം": 1000,
        "ലക്ഷം": 100_000,
        "കോടി": 10_000_000,
    }

    _ROMANIZED_HINDI: dict[str, int] = {
        "ek": 1,
        "do": 2,
        "teen": 3,
        "char": 4,
        "paanch": 5,
        "panch": 5,
        "chhe": 6,
        "saat": 7,
        "aath": 8,
        "nau": 9,
        "das": 10,
        "bees": 20,
        "tees": 30,
        "chaalis": 40,
        "pachaas": 50,
        "pachas": 50,
        "saath": 60,
        "sattar": 70,
        "assi": 80,
        "nabbe": 90,
        "sau": 100,
        "hazaar": 1000,
        "hazar": 1000,
        "lakh": 100_000,
        "crore": 10_000_000,
    }

    def __init__(self) -> None:
        self._word_map: dict[str, int] = {}
        for mapping in (
            self._ENGLISH_WORDS,
            self._HINDI_WORDS,
            self._MALAYALAM_WORDS,
            self._ROMANIZED_HINDI,
        ):
            self._word_map.update(mapping)

    def parse_int(self, text: str) -> int | None:
        """Parse a number from digits or spoken words."""
        if text is None:
            return None
        cleaned = str(text).strip()
        if not cleaned:
            return None

        if re.fullmatch(r"[\d,]+", cleaned):
            try:
                return int(cleaned.replace(",", ""))
            except ValueError:
                return None

        if re.fullmatch(r"[\d.]+", cleaned):
            try:
                return int(float(cleaned))
            except ValueError:
                return None

        tokens = re.findall(r"[\w\u0900-\u097F\u0D00-\u0D7F]+", cleaned.lower())
        if not tokens:
            return None

        return self._parse_word_tokens(tokens)

    def parse_decimal(self, text: str) -> Decimal | None:
        """Parse a decimal value from digits or spoken words."""
        if text is None:
            return None
        cleaned = str(text).strip()
        if not cleaned:
            return None

        if re.fullmatch(r"[\d.,]+", cleaned):
            try:
                return Decimal(cleaned.replace(",", ""))
            except InvalidOperation:
                return None

        parsed = self.parse_int(cleaned)
        if parsed is not None:
            return Decimal(parsed)
        return None

    def _parse_word_tokens(self, tokens: list[str]) -> int | None:
        total = 0
        current = 0

        for token in tokens:
            value = self._word_map.get(token)
            if value is None:
                return None

            if value >= 1000:
                if current == 0:
                    current = 1
                current *= value
                total += current
                current = 0
            elif value == 100:
                current = (current or 1) * value
            else:
                current += value

        return total + current
