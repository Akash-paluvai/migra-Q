"""Unit tests for BoundaryClassifier."""

from backend.diagnosis.models import DiscrepancyCategory
from backend.diagnosis.rules.boundary import BoundaryClassifier
from backend.diagnosis.signals import RawDiscrepancySignal


def test_boundary_classifier_priority():
    clf = BoundaryClassifier()
    assert clf.priority == 2
    assert clf.category == DiscrepancyCategory.BOUNDARY_CONDITION


def test_boundary_greater_than_vs_greater_equal():
    clf = BoundaryClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        source_expression="amount > 500",
        target_expression="amount >= 500",
    )
    assert clf.matches(sig, [sig]) is True
    cand = clf.classify(sig, [sig])
    assert cand.category == DiscrepancyCategory.BOUNDARY_CONDITION
    assert cand.subcategory == "OPERATOR_INCLUSION"


def test_boundary_less_than_vs_less_equal():
    clf = BoundaryClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        source_expression="amount < 100",
        target_expression="amount <= 100",
    )
    assert clf.matches(sig, [sig]) is True
    cand = clf.classify(sig, [sig])
    assert cand.category == DiscrepancyCategory.BOUNDARY_CONDITION


def test_boundary_between_clause():
    clf = BoundaryClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="RULE_DIFF",
        source_expression="amount BETWEEN 10 AND 50",
        target_expression="amount >= 10 AND amount < 50",
    )
    assert clf.matches(sig, [sig]) is True


def test_boundary_payload_operator_changed():
    clf = BoundaryClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="RULE_MISMATCH",
        payload={"category": "OPERATOR_CHANGED", "source_value": ">", "target_value": ">="},
    )
    assert clf.matches(sig, [sig]) is True


def test_boundary_does_not_match_equals_vs_not_equals():
    clf = BoundaryClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="FILTER_DIFF",
        source_expression="status = 'ACTIVE'",
        target_expression="status != 'INACTIVE'",
    )
    assert clf.matches(sig, [sig]) is False


def test_boundary_reason_template():
    clf = BoundaryClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        source_expression="x > 5",
        target_expression="x >= 5",
    )
    cand = clf.classify(sig, [sig])
    assert "inclusivity" in cand.reason_template


def test_boundary_analysis_path():
    clf = BoundaryClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        analysis_path="business_rules[0].condition",
        source_expression="x > 5",
        target_expression="x >= 5",
    )
    cand = clf.classify(sig, [sig])
    assert cand.analysis_path == "business_rules[0].condition"


def test_boundary_candidate_priority():
    clf = BoundaryClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        source_expression="x > 5",
        target_expression="x >= 5",
    )
    cand = clf.classify(sig, [sig])
    assert cand.priority == 2


def test_boundary_candidate_payload_preservation():
    clf = BoundaryClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        payload={"boundary_val": 500},
    )
    cand = clf.classify(sig, [sig])
    assert cand.payload["boundary_val"] == 500
