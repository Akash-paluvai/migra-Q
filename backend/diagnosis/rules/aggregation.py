"""Priority 4: Aggregation Semantics Classifier."""

from backend.diagnosis.models import ClassificationMethod, DiscrepancyCategory
from backend.diagnosis.rules.base import BaseRuleClassifier, ClassificationCandidate
from backend.diagnosis.signals import RawDiscrepancySignal


class AggregationClassifier(BaseRuleClassifier):
    @property
    def priority(self) -> int:
        return 4

    @property
    def category(self) -> DiscrepancyCategory:
        return DiscrepancyCategory.AGGREGATION_SEMANTICS

    def matches(self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]) -> bool:
        src = (signal.source_expression or "").upper()
        tgt = (signal.target_expression or "").upper()

        if signal.signal_type in (
            "AGGREGATION_DIFF",
            "AGGREGATE_MISMATCH",
            "AGGREGATE_RESULT_DIFF",
        ):
            return True
        if any(fn in src or fn in tgt for fn in ("SUM(", "AVG(", "COUNT(", "MIN(", "MAX(")):
            return True
        if "GROUP BY" in src or "GROUP BY" in tgt or "HAVING" in src or "HAVING" in tgt:
            return True
        return False

    def classify(
        self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]
    ) -> ClassificationCandidate:
        src = signal.source_expression or str(signal.payload.get("source_value", ""))
        tgt = signal.target_expression or str(signal.payload.get("target_value", ""))

        reason = f"Aggregation logic or grouping differs: '{src}' vs '{tgt}'."

        return ClassificationCandidate(
            category=DiscrepancyCategory.AGGREGATION_SEMANTICS,
            subcategory="AGGREGATE_FUNCTION_OR_GROUPING_CHANGED",
            priority=self.priority,
            source_expression=src,
            target_expression=tgt,
            analysis_path=signal.analysis_path or "aggregations[0]",
            classification_method=ClassificationMethod.COMBINED_DETERMINISTIC,
            reason_template=reason,
            payload=signal.payload,
        )
