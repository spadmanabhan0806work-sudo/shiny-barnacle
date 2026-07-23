from __future__ import annotations


def accuracy(correct: int, total: int) -> float:
    if total == 0:
        return 0.0
    return correct / total


def precision(true_positives: int, false_positives: int) -> float:
    denominator = true_positives + false_positives
    if denominator == 0:
        return 0.0
    return true_positives / denominator


def recall(true_positives: int, false_negatives: int) -> float:
    denominator = true_positives + false_negatives
    if denominator == 0:
        return 0.0
    return true_positives / denominator


def f1_score(precision_value: float, recall_value: float) -> float:
    denominator = precision_value + recall_value
    if denominator == 0:
        return 0.0
    return 2 * precision_value * recall_value / denominator
