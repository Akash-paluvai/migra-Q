"""Priority 7: Case Logic Classifier."""

from backend.diagnosis.models import ClassificationMethod, DiscrepancyCategory
from backend.diagnosis.rules.base import BaseRuleClassifier, ClassificationCandidate
from backend.diagnosis.signals import RawDiscrepancySignal


class CaseLogicClassifier(BaseRuleClassifier):
    @property
    def priority(self) -> int:
        return 7

    @property
    def category(self) -> DiscrepancyCategory:
        return DiscrepancyCategory.CASE_LOGIC

    def matches(self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]) -> bool:
        src = (signal.source_expression or "").upper()
        tgt = (signal.target_expression or "").upper()

        if (
            "CASE" in src
            or "CASE" in tgt
            or signal.signal_type in ("CASE_RULE_CHANGED", "CASE_BRANCH_DIFF")
        ):
            return True
        return False

    def classify(
        self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]
    ) -> ClassificationCandidate:
        src = signal.source_expression or ""
        tgt = signal.target_expression or ""

        reason = f"Conditional CASE/WHEN evaluation branches differ: '{src}' vs '{tgt}'."

        return ClassificationCandidate(
            category=DiscrepancyCategory.CASE_LOGIC,
            subcategory="CASE_BRANCH_CONDITION_CHANGED",
            priority=self.priority,
            source_expression=src,
            target_expression=tgt,
            analysis_path=signal.analysis_path or "business_rules[0]",
            classification_method=ClassificationMethod.COMBINED_DETERMINISTIC,
            reason_template=reason,
            payload=signal.payload,
        )
