"""Priority 5: Date Semantics Classifier."""

from backend.diagnosis.models import ClassificationMethod, DiscrepancyCategory
from backend.diagnosis.rules.base import BaseRuleClassifier, ClassificationCandidate
from backend.diagnosis.signals import RawDiscrepancySignal


class DateSemanticsClassifier(BaseRuleClassifier):
    @property
    def priority(self) -> int:
        return 5

    @property
    def category(self) -> DiscrepancyCategory:
        return DiscrepancyCategory.DATE_SEMANTICS

    def matches(self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]) -> bool:
        src = (signal.source_expression or "").upper()
        tgt = (signal.target_expression or "").upper()

        keywords = (
            "DATE",
            "TIME",
            "TIMESTAMP",
            "DATE_TRUNC",
            "TRUNC",
            "EXTRACT",
            "YEAR",
            "MONTH",
            "DAY",
            "INTERVAL",
        )
        if any(kw in src or kw in tgt for kw in keywords):
            return True
        return False

    def classify(
        self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]
    ) -> ClassificationCandidate:
        src = signal.source_expression or ""
        tgt = signal.target_expression or ""

        reason = (
            f"Date/time evaluation semantics differ between source ('{src}') and target ('{tgt}')."
        )

        return ClassificationCandidate(
            category=DiscrepancyCategory.DATE_SEMANTICS,
            subcategory="DATE_TRUNC_OR_INTERVAL_CHANGED",
            priority=self.priority,
            source_expression=src,
            target_expression=tgt,
            analysis_path=signal.analysis_path or "expressions[date]",
            classification_method=ClassificationMethod.COMBINED_DETERMINISTIC,
            reason_template=reason,
            payload=signal.payload,
        )
