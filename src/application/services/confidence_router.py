from __future__ import annotations

from dataclasses import dataclass

from src.domain.services.intent_validator import ValidatedIntent


@dataclass
class ConfidenceSignals:
    llm_confidence: float
    validation_penalty: float
    stock_match_confidence: float
    signals: dict[str, float]


@dataclass
class RoutingDecision:
    final_confidence: float
    requires_review: bool
    signals: ConfidenceSignals


class ConfidenceRouter:
    """Multi-signal confidence scoring and HITL routing."""

    def __init__(self, threshold: float = 0.85) -> None:
        self._threshold = threshold

    @property
    def threshold(self) -> float:
        return self._threshold

    def route(
        self,
        llm_confidence: float,
        validated: ValidatedIntent,
    ) -> RoutingDecision:
        validation_penalty = min(len(validated.validation_notes) * 0.08, 0.4)
        stock_conf = validated.stock_match_confidence

        final = (
            llm_confidence * 0.5
            + stock_conf * 0.3
            + max(0.0, 1.0 - validation_penalty) * 0.2
        )
        final = max(0.0, min(1.0, final))

        signals = ConfidenceSignals(
            llm_confidence=llm_confidence,
            validation_penalty=validation_penalty,
            stock_match_confidence=stock_conf,
            signals={
                "llm": llm_confidence,
                "stock_match": stock_conf,
                "validation": max(0.0, 1.0 - validation_penalty),
                "final": final,
            },
        )

        return RoutingDecision(
            final_confidence=final,
            requires_review=final < self._threshold,
            signals=signals,
        )
