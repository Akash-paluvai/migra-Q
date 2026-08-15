"""Priority 6: Type Conversion Classifier."""

from backend.diagnosis.models import ClassificationMethod, DiscrepancyCategory
from backend.diagnosis.rules.base import BaseRuleClassifier, ClassificationCandidate
from backend.diagnosis.signals import RawDiscrepancySignal


class TypeConversionClassifier(BaseRuleClassifier):
    @property
    def priority(self) -> int:
        return 6

    @property
    def category(self) -> DiscrepancyCategory:
        return DiscrepancyCategory.TYPE_CONVERSION

    def matches(self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]) -> bool:
        src = (signal.source_expression or "").upper()
        tgt = (signal.target_expression or "").upper()

        if "CAST(" in src or "CAST(" in tgt or "CONVERT" in src or "CONVERT" in tgt:
            return True
        if signal.signal_type in ("SCHEMA_TYPE_CHANGED", "TYPE_DIFF"):
            return True
        return False

    def classify(
        self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]
    ) -> ClassificationCandidate:
        src = signal.source_expression or ""
        tgt = signal.target_expression or ""

        reason = f"Data type casting or representation differs: '{src}' vs '{tgt}'."

        return ClassificationCandidate(
            category=DiscrepancyCategory.TYPE_CONVERSION,
            subcategory="CAST_OR_COERCION_CHANGED",
            priority=self.priority,
            source_expression=src,
            target_expression=tgt,
            analysis_path=signal.analysis_path or "columns[type]",
            classification_method=ClassificationMethod.COMBINED_DETERMINISTIC,
            reason_template=reason,
            payload=signal.payload,
        )
