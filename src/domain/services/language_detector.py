from __future__ import annotations

import re

from src.domain.value_objects.language import Language

# Unicode ranges for script detection
_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_MALAYALAM = re.compile(r"[\u0D00-\u0D7F]")
_GUJARATI = re.compile(r"[\u0A80-\u0AFF]")
_LATIN = re.compile(r"[A-Za-z]")


# Common romanized Hindi/Malayalam tokens indicating code-mixed speech
_ROMANIZED_INDIC = re.compile(
    r"\b("
    r"mujhe|mera|meri|kya|hai|hain|karne|karna|chahiye|"
    r"rupees|rupaye|sau|hazaar|khareed|bech|"
    r"njan|enikku|venam"
    r")\b",
    re.IGNORECASE,
)


def detect_language(text: str, *, provider_hint: str | None = None) -> str:
    """Detect language code: en, hi, ml, gu, mixed, or unknown."""
    if provider_hint:
        normalized = _normalize_provider_hint(provider_hint)
        if normalized != Language.UNKNOWN.value:
            return normalized

    if not text or not text.strip():
        return Language.UNKNOWN.value

    has_latin = bool(_LATIN.search(text))
    has_devanagari = bool(_DEVANAGARI.search(text))
    has_malayalam = bool(_MALAYALAM.search(text))
    has_gujarati = bool(_GUJARATI.search(text))
    has_romanized_indic = bool(_ROMANIZED_INDIC.search(text))

    scripts = sum([has_latin, has_devanagari, has_malayalam, has_gujarati])
    if scripts >= 2 or (has_latin and (has_devanagari or has_malayalam or has_gujarati)):
        return Language.MIXED.value
    if has_romanized_indic and has_latin:
        return Language.MIXED.value
    if has_malayalam:
        return Language.MALAYALAM.value
    if has_gujarati:
        return Language.GUJARATI.value
    if has_devanagari:
        return Language.HINDI.value
    if has_latin:
        return Language.ENGLISH.value
    return Language.UNKNOWN.value


def _normalize_provider_hint(hint: str) -> str:
    code = hint.lower().split("-")[0]
    if code in ("en", "hi", "ml", "gu", "mixed"):
        return code
    return Language.from_code(code).value
