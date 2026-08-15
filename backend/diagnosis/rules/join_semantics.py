"""Priority 3: Join Semantics Classifier."""

from backend.diagnosis.models import ClassificationMethod, DiscrepancyCategory
from backend.diagnosis.rules.base import BaseRuleClassifier, ClassificationCandidate
from backend.diagnosis.signals import RawDiscrepancySignal


class JoinSemanticsClassifier(BaseRuleClassifier):
    @property
    def priority(self) -> int:
        return 3

    @property
    def category(self) -> DiscrepancyCategory:
        return DiscrepancyCategory.JOIN_SEMANTICS

    def matches(self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]) -> bool:
        src = (signal.source_expression or "").upper()
        tgt = (signal.target_expression or "").upper()

        if (
            "JOIN" in src
            or "JOIN" in tgt
            or signal.signal_type in ("JOIN_DIFF", "JOIN_TYPE_CHANGED", "JOIN_CONDITION_CHANGED")
        ):
            return True
        if signal.payload.get("category") in ("JOIN_TYPE_CHANGED", "JOIN_CONDITION_CHANGED"):
            return True
        return False

    def classify(
        self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]
    ) -> ClassificationCandidate:
        src = signal.source_expression or str(signal.payload.get("source_value", ""))
        tgt = signal.target_expression or str(signal.payload.get("target_value", ""))

        reason = f"Relational join semantics differ between source ('{src}') and target ('{tgt}')."

        return ClassificationCandidate(
            category=DiscrepancyCategory.JOIN_SEMANTICS,
            subcategory="JOIN_TYPE_OR_CONDITION_CHANGED",
            priority=self.priority,
            source_expression=src,
            target_expression=tgt,
            analysis_path=signal.analysis_path or "joins[0]",
            classification_method=ClassificationMethod.COMBINED_DETERMINISTIC,
            reason_template=reason,
            payload=signal.payload,
        )
