"""Priority 9: Column Mapping Classifier."""

from backend.diagnosis.models import ClassificationMethod, DiscrepancyCategory
from backend.diagnosis.rules.base import BaseRuleClassifier, ClassificationCandidate
from backend.diagnosis.signals import RawDiscrepancySignal


class ColumnMappingClassifier(BaseRuleClassifier):
    @property
    def priority(self) -> int:
        return 9

    @property
    def category(self) -> DiscrepancyCategory:
        return DiscrepancyCategory.COLUMN_MAPPING

    def matches(self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]) -> bool:
        if signal.signal_type in (
            "COLUMN_MAPPING_CHANGED",
            "SCHEMA_COLUMN_ADDED",
            "SCHEMA_COLUMN_REMOVED",
            "COLUMN_SHIFT",
        ):
            return True
        if "COLUMN_MAPPING" in signal.signal_type or "mapping" in signal.analysis_path:
            return True
        return False

    def classify(
        self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]
    ) -> ClassificationCandidate:
        src = signal.source_expression or ""
        tgt = signal.target_expression or ""

        reason = f"Source output column '{src}' mapped to different target column '{tgt}'."

        return ClassificationCandidate(
            category=DiscrepancyCategory.COLUMN_MAPPING,
            subcategory="OUTPUT_COLUMN_SHIFT",
            priority=self.priority,
            source_expression=src,
            target_expression=tgt,
            analysis_path=signal.analysis_path or "columns[mapping]",
            classification_method=ClassificationMethod.COMBINED_DETERMINISTIC,
            reason_template=reason,
            payload=signal.payload,
        )
