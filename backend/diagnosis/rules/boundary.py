"""Priority 2: Boundary Condition Classifier."""

from backend.diagnosis.models import ClassificationMethod, DiscrepancyCategory
from backend.diagnosis.rules.base import BaseRuleClassifier, ClassificationCandidate
from backend.diagnosis.signals import RawDiscrepancySignal

BOUNDARY_OPS = {">", ">=", "<", "<=", "BETWEEN"}


class BoundaryClassifier(BaseRuleClassifier):
    @property
    def priority(self) -> int:
        return 2

    @property
    def category(self) -> DiscrepancyCategory:
        return DiscrepancyCategory.BOUNDARY_CONDITION

    def matches(self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]) -> bool:
        src = signal.source_expression or str(signal.payload.get("source_value", ""))
        tgt = signal.target_expression or str(signal.payload.get("target_value", ""))

        if (">" in src and ">=" in tgt) or (">=" in src and ">" in tgt):
            return True
        if ("<" in src and "<=" in tgt) or ("<=" in src and "<" in tgt):
            return True
        if "BETWEEN" in src.upper() or "BETWEEN" in tgt.upper():
            return True

        return False

    def classify(
        self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]
    ) -> ClassificationCandidate:
        src = signal.source_expression or str(signal.payload.get("source_value", ""))
        tgt = signal.target_expression or str(signal.payload.get("target_value", ""))

        reason = (
            f"Source and target use identical operands but differ in boundary inclusivity: "
            f"'{src}' vs '{tgt}'."
        )

        return ClassificationCandidate(
            category=DiscrepancyCategory.BOUNDARY_CONDITION,
            subcategory="OPERATOR_INCLUSION",
            priority=self.priority,
            source_expression=src,
            target_expression=tgt,
            analysis_path=signal.analysis_path or "business_rules[0].condition.operator",
            classification_method=ClassificationMethod.COMBINED_DETERMINISTIC,
            reason_template=reason,
            payload=signal.payload,
        )
