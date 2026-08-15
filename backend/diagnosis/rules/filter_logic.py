"""Priority 8: Filter Logic Classifier."""

from backend.diagnosis.models import ClassificationMethod, DiscrepancyCategory
from backend.diagnosis.rules.base import BaseRuleClassifier, ClassificationCandidate
from backend.diagnosis.signals import RawDiscrepancySignal


class FilterLogicClassifier(BaseRuleClassifier):
    @property
    def priority(self) -> int:
        return 8

    @property
    def category(self) -> DiscrepancyCategory:
        return DiscrepancyCategory.FILTER_LOGIC

    def matches(self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]) -> bool:
        if signal.signal_type in (
            "FILTER_DIFF",
            "FILTER_ADDED",
            "FILTER_REMOVED",
            "FILTER_EXPRESSION_CHANGED",
        ):
            return True
        if "WHERE" in signal.analysis_path.upper() or "FILTER" in signal.analysis_path.upper():
            return True
        return False

    def classify(
        self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]
    ) -> ClassificationCandidate:
        src = signal.source_expression or ""
        tgt = signal.target_expression or ""

        reason = (
            f"Boolean filter predicate logic differs between source ('{src}') and target ('{tgt}')."
        )

        return ClassificationCandidate(
            category=DiscrepancyCategory.FILTER_LOGIC,
            subcategory="FILTER_PREDICATE_CHANGED",
            priority=self.priority,
            source_expression=src,
            target_expression=tgt,
            analysis_path=signal.analysis_path or "filters[0]",
            classification_method=ClassificationMethod.COMBINED_DETERMINISTIC,
            reason_template=reason,
            payload=signal.payload,
        )
