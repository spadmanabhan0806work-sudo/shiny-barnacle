from dataclasses import dataclass


@dataclass(frozen=True)
class Confidence:
    """Calibrated confidence score between 0.0 and 1.0."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.value}")

    @property
    def is_high(self) -> bool:
        return self.value >= 0.85

    @property
    def is_low(self) -> bool:
        return self.value < 0.85
