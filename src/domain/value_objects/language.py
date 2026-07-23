from enum import Enum


class Language(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    MALAYALAM = "ml"
    GUJARATI = "gu"
    MIXED = "mixed"
    UNKNOWN = "unknown"
    OTHER = "other"

    @classmethod
    def from_code(cls, code: str) -> "Language":
        try:
            return cls(code.lower())
        except ValueError:
            return cls.UNKNOWN
