"""Discrepancy Classifier Registry Manager."""

from backend.diagnosis.rules import CLASSIFIERS, BaseRuleClassifier, ClassificationCandidate
from backend.diagnosis.signals import RawDiscrepancySignal


class DiscrepancyClassifier:
    """Evaluates raw discrepancy signals against registered priority classifiers."""

    def __init__(self, classifiers: list[BaseRuleClassifier] | None = None) -> None:
        self.classifiers = classifiers or CLASSIFIERS

    def classify_signal(
        self,
        signal: RawDiscrepancySignal,
        signals: list[RawDiscrepancySignal],
    ) -> ClassificationCandidate:
        """Find highest priority matching classifier for a signal."""
        # Sort classifiers by priority rank (1 = highest)
        sorted_classifiers = sorted(self.classifiers, key=lambda c: c.priority)

        for clf in sorted_classifiers:
            if clf.matches(signal, signals):
                return clf.classify(signal, signals)

        # Fallback to Generic (UNKNOWN) if no classifier matched
        fallback = sorted_classifiers[-1]
        return fallback.classify(signal, signals)
