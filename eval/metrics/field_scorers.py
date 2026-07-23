from __future__ import annotations

from dataclasses import dataclass, field

from eval.metrics.core import accuracy, f1_score, precision, recall

FIELD_NAMES = ("side", "stock_symbol", "quantity", "price", "exchange")


@dataclass
class FieldMetrics:
    field: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    correct: int
    total: int
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0


@dataclass
class FieldComparison:
    matches: dict[str, bool] = field(default_factory=dict)


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def _normalize_side(value: object) -> str:
    return str(value or "").strip().upper()


def _normalize_exchange(value: object) -> str:
    return str(value or "").strip().upper()


def _normalize_stock(value: object) -> str:
    return str(value or "").strip().upper()


def _normalize_quantity(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_price(value: object) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def field_match(field: str, gold: object, prediction: object) -> bool:
    if field == "side":
        return _normalize_side(gold) == _normalize_side(prediction)
    if field == "exchange":
        return _normalize_exchange(gold) == _normalize_exchange(prediction)
    if field == "stock_symbol":
        g = _normalize_stock(gold)
        p = _normalize_stock(prediction)
        if not g or not p:
            return False
        return g == p or _levenshtein(g, p) <= 1
    if field == "quantity":
        g = _normalize_quantity(gold)
        p = _normalize_quantity(prediction)
        return g is not None and g == p
    if field == "price":
        g = _normalize_price(gold)
        p = _normalize_price(prediction)
        return g is not None and p is not None and abs(g - p) <= 0.011
    raise ValueError(f"Unknown field: {field}")


def compare_fields(gold: dict, prediction: dict) -> FieldComparison:
    return FieldComparison(
        matches={name: field_match(name, gold.get(name), prediction.get(name)) for name in FIELD_NAMES}
    )


def _score_categorical_field(
    field: str,
    pairs: list[tuple[dict, dict]],
    *,
    normalizer,
) -> FieldMetrics:
    total = len(pairs)
    correct = 0
    labels: set[str] = set()
    for gold, pred in pairs:
        labels.add(normalizer(gold.get(field)))
        labels.add(normalizer(pred.get(field)))

    tp = fp = fn = 0
    for gold, pred in pairs:
        g = normalizer(gold.get(field))
        p = normalizer(pred.get(field))
        if g == p:
            correct += 1
        for label in labels:
            if not label:
                continue
            gold_is = g == label
            pred_is = p == label
            if gold_is and pred_is:
                tp += 1
            elif pred_is and not gold_is:
                fp += 1
            elif gold_is and not pred_is:
                fn += 1

    prec = precision(tp, fp)
    rec = recall(tp, fn)
    return FieldMetrics(
        field=field,
        accuracy=accuracy(correct, total),
        precision=prec,
        recall=rec,
        f1=f1_score(prec, rec),
        correct=correct,
        total=total,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
    )


def score_field(field: str, pairs: list[tuple[dict, dict]]) -> FieldMetrics:
    if not pairs:
        return FieldMetrics(field=field, accuracy=0.0, precision=0.0, recall=0.0, f1=0.0, correct=0, total=0)

    if field in ("side", "exchange"):
        normalizer = _normalize_side if field == "side" else _normalize_exchange
        return _score_categorical_field(field, pairs, normalizer=normalizer)

    total = len(pairs)
    correct = sum(1 for gold, pred in pairs if field_match(field, gold.get(field), pred.get(field)))
    prec = rec = accuracy(correct, total)
    return FieldMetrics(
        field=field,
        accuracy=accuracy(correct, total),
        precision=prec,
        recall=rec,
        f1=f1_score(prec, rec),
        correct=correct,
        total=total,
        true_positives=correct,
        false_positives=total - correct,
        false_negatives=total - correct,
    )


def score_all_fields(pairs: list[tuple[dict, dict]]) -> dict[str, FieldMetrics]:
    return {name: score_field(name, pairs) for name in FIELD_NAMES}
