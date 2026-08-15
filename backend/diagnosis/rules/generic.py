"""Priority 10 & 11: Set Semantics and Generic Unknown Classifiers."""

from backend.diagnosis.models import ClassificationMethod, DiscrepancyCategory
from backend.diagnosis.rules.base import BaseRuleClassifier, ClassificationCandidate
from backend.diagnosis.signals import RawDiscrepancySignal


class SetSemanticsClassifier(BaseRuleClassifier):
    @property
    def priority(self) -> int:
        return 10

    @property
    def category(self) -> DiscrepancyCategory:
        return DiscrepancyCategory.SET_SEMANTICS

    def matches(self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]) -> bool:
        src = (signal.source_expression or "").upper()
        tgt = (signal.target_expression or "").upper()

        if "UNION" in src or "UNION" in tgt or "INTERSECT" in src or "EXCEPT" in tgt:
            return True
        return False

    def classify(
        self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]
    ) -> ClassificationCandidate:
        src = signal.source_expression or ""
        tgt = signal.target_expression or ""

        reason = f"Set-operation duplicate handling semantics differ: '{src}' vs '{tgt}'."

        return ClassificationCandidate(
            category=DiscrepancyCategory.SET_SEMANTICS,
            subcategory="UNION_OR_SET_OPERATOR_CHANGED",
            priority=self.priority,
            source_expression=src,
            target_expression=tgt,
            analysis_path=signal.analysis_path or "set_operations[0]",
            classification_method=ClassificationMethod.COMBINED_DETERMINISTIC,
            reason_template=reason,
            payload=signal.payload,
        )


class GenericClassifier(BaseRuleClassifier):
    @property
    def priority(self) -> int:
        return 11

    @property
    def category(self) -> DiscrepancyCategory:
        return DiscrepancyCategory.UNKNOWN

    def matches(self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]) -> bool:
        return True  # Fallback rule matches everything

    def classify(
        self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]
    ) -> ClassificationCandidate:
        src = signal.source_expression or str(signal.payload.get("source_value", ""))
        tgt = signal.target_expression or str(signal.payload.get("target_value", ""))

        reason = (
            f"Insufficient evidence for specific taxonomy category difference: '{src}' vs '{tgt}'."
        )

        return ClassificationCandidate(
            category=DiscrepancyCategory.UNKNOWN,
            subcategory="UNCLASSIFIED_DISCREPANCY",
            priority=self.priority,
            source_expression=src,
            target_expression=tgt,
            analysis_path=signal.analysis_path or "unspecified",
            classification_method=ClassificationMethod.UNKNOWN,
            reason_template=reason,
            payload=signal.payload,
        )
