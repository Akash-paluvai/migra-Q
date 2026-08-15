"""Priority 1: Null Semantics Classifier."""

from backend.diagnosis.models import ClassificationMethod, DiscrepancyCategory
from backend.diagnosis.rules.base import BaseRuleClassifier, ClassificationCandidate
from backend.diagnosis.signals import RawDiscrepancySignal


class NullSemanticsClassifier(BaseRuleClassifier):
    @property
    def priority(self) -> int:
        return 1

    @property
    def category(self) -> DiscrepancyCategory:
        return DiscrepancyCategory.NULL_SEMANTICS

    def matches(self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]) -> bool:
        src = (signal.source_expression or "").upper()
        tgt = (signal.target_expression or "").upper()

        if "IS NULL" in src or "IS NULL" in tgt or "NULL" in src or "NULL" in tgt:
            return True
        if "COALESCE" in src or "COALESCE" in tgt or "NVL" in src or "IFNULL" in tgt:
            return True
        if ("COUNT(*)" in src and "COUNT(" in tgt and "COUNT(*)" not in tgt) or (
            "COUNT(*)" in tgt and "COUNT(" in src and "COUNT(*)" not in src
        ):
            return True
        if signal.signal_type == "NULL_SEMANTICS_CHANGED":
            return True
        return False

    def classify(
        self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]
    ) -> ClassificationCandidate:
        src = signal.source_expression or ""
        tgt = signal.target_expression or ""

        reason = (
            f"Source expression '{src}' and target expression '{tgt}' "
            f"differ in SQL NULL handling semantics."
        )

        return ClassificationCandidate(
            category=DiscrepancyCategory.NULL_SEMANTICS,
            subcategory="NULL_TREATMENT_DIVERGENCE",
            priority=self.priority,
            source_expression=src,
            target_expression=tgt,
            analysis_path=signal.analysis_path or "filters[0]",
            classification_method=ClassificationMethod.COMBINED_DETERMINISTIC,
            reason_template=reason,
            payload=signal.payload,
        )
