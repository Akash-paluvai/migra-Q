"""Classifier registry containing all priority rule classifiers."""

from backend.diagnosis.rules.aggregation import AggregationClassifier
from backend.diagnosis.rules.base import BaseRuleClassifier, ClassificationCandidate
from backend.diagnosis.rules.boundary import BoundaryClassifier
from backend.diagnosis.rules.case_logic import CaseLogicClassifier
from backend.diagnosis.rules.column_mapping import ColumnMappingClassifier
from backend.diagnosis.rules.date_semantics import DateSemanticsClassifier
from backend.diagnosis.rules.filter_logic import FilterLogicClassifier
from backend.diagnosis.rules.generic import GenericClassifier, SetSemanticsClassifier
from backend.diagnosis.rules.join_semantics import JoinSemanticsClassifier
from backend.diagnosis.rules.null_semantics import NullSemanticsClassifier
from backend.diagnosis.rules.type_conversion import TypeConversionClassifier

CLASSIFIERS: list[BaseRuleClassifier] = [
    NullSemanticsClassifier(),  # Priority 1: NULL precedence over aggregation
    BoundaryClassifier(),  # Priority 2: Operator inclusion (> vs >=)
    JoinSemanticsClassifier(),  # Priority 3: INNER vs LEFT, key changes
    AggregationClassifier(),  # Priority 4: SUM vs SUM DISTINCT, GROUP BY
    DateSemanticsClassifier(),  # Priority 5: DATE_TRUNC, month boundaries
    TypeConversionClassifier(),  # Priority 6: CAST, type coercions
    CaseLogicClassifier(),  # Priority 7: CASE branch conditions
    FilterLogicClassifier(),  # Priority 8: AND vs OR, filter add/remove
    ColumnMappingClassifier(),  # Priority 9: Column shift
    SetSemanticsClassifier(),  # Priority 10: UNION vs UNION ALL
    GenericClassifier(),  # Priority 11: UNKNOWN fallback
]

__all__ = [
    "BaseRuleClassifier",
    "ClassificationCandidate",
    "CLASSIFIERS",
    "NullSemanticsClassifier",
    "BoundaryClassifier",
    "JoinSemanticsClassifier",
    "AggregationClassifier",
    "DateSemanticsClassifier",
    "TypeConversionClassifier",
    "CaseLogicClassifier",
    "FilterLogicClassifier",
    "ColumnMappingClassifier",
    "SetSemanticsClassifier",
    "GenericClassifier",
]
