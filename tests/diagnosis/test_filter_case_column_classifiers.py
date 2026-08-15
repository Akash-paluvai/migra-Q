"""Unit tests for Filter, Case, Column, Set, and Generic Classifiers."""

from backend.diagnosis.models import DiscrepancyCategory
from backend.diagnosis.rules.case_logic import CaseLogicClassifier
from backend.diagnosis.rules.column_mapping import ColumnMappingClassifier
from backend.diagnosis.rules.filter_logic import FilterLogicClassifier
from backend.diagnosis.rules.generic import GenericClassifier, SetSemanticsClassifier
from backend.diagnosis.signals import RawDiscrepancySignal


def test_filter_classifier_priority_and_category():
    clf = FilterLogicClassifier()
    assert clf.priority == 8
    assert clf.category == DiscrepancyCategory.FILTER_LOGIC


def test_filter_added_or_removed():
    clf = FilterLogicClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="FILTER_ADDED",
        source_expression="",
        target_expression="status = 'ACTIVE'",
    )
    assert clf.matches(sig, [sig]) is True
    cand = clf.classify(sig, [sig])
    assert cand.category == DiscrepancyCategory.FILTER_LOGIC


def test_case_logic_classifier():
    clf = CaseLogicClassifier()
    assert clf.priority == 7
    assert clf.category == DiscrepancyCategory.CASE_LOGIC

    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="CASE_RULE_CHANGED",
        source_expression="CASE WHEN x=1 THEN 'A' ELSE 'B' END",
        target_expression="CASE WHEN x=1 THEN 'A' WHEN x=2 THEN 'C' ELSE 'B' END",
    )
    assert clf.matches(sig, [sig]) is True
    cand = clf.classify(sig, [sig])
    assert cand.category == DiscrepancyCategory.CASE_LOGIC


def test_column_mapping_classifier():
    clf = ColumnMappingClassifier()
    assert clf.priority == 9
    assert clf.category == DiscrepancyCategory.COLUMN_MAPPING

    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="COLUMN_MAPPING_CHANGED",
        source_expression="customer_id",
        target_expression="account_id",
    )
    assert clf.matches(sig, [sig]) is True
    cand = clf.classify(sig, [sig])
    assert cand.category == DiscrepancyCategory.COLUMN_MAPPING


def test_set_semantics_classifier():
    clf = SetSemanticsClassifier()
    assert clf.priority == 10
    assert clf.category == DiscrepancyCategory.SET_SEMANTICS

    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="RULE_DIFF",
        source_expression="SELECT * FROM t1 UNION SELECT * FROM t2",
        target_expression="SELECT * FROM t1 UNION ALL SELECT * FROM t2",
    )
    assert clf.matches(sig, [sig]) is True
    cand = clf.classify(sig, [sig])
    assert cand.category == DiscrepancyCategory.SET_SEMANTICS


def test_generic_classifier_fallback():
    clf = GenericClassifier()
    assert clf.priority == 11
    assert clf.category == DiscrepancyCategory.UNKNOWN

    sig = RawDiscrepancySignal(
        source_validator="UnknownValidator",
        signal_type="UNKNOWN_SIGNAL",
        source_expression="foo()",
        target_expression="bar()",
    )
    assert clf.matches(sig, [sig]) is True
    cand = clf.classify(sig, [sig])
    assert cand.category == DiscrepancyCategory.UNKNOWN
