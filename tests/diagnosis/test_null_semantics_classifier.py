"""Unit tests for NullSemanticsClassifier."""

from backend.diagnosis.models import DiscrepancyCategory
from backend.diagnosis.rules.null_semantics import NullSemanticsClassifier
from backend.diagnosis.signals import RawDiscrepancySignal


def test_null_classifier_priority():
    clf = NullSemanticsClassifier()
    assert clf.priority == 1
    assert clf.category == DiscrepancyCategory.NULL_SEMANTICS


def test_null_is_null_vs_equals_null():
    clf = NullSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="NULL_SEMANTICS_CHANGED",
        source_expression="closed_at IS NULL",
        target_expression="closed_at = NULL",
    )
    assert clf.matches(sig, [sig]) is True
    cand = clf.classify(sig, [sig])
    assert cand.category == DiscrepancyCategory.NULL_SEMANTICS
    assert cand.subcategory == "NULL_TREATMENT_DIVERGENCE"


def test_null_coalesce_difference():
    clf = NullSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="FILTER_DIFF",
        source_expression="COALESCE(status, 'UNKNOWN')",
        target_expression="status",
    )
    assert clf.matches(sig, [sig]) is True


def test_null_count_star_vs_count_column():
    clf = NullSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="AGGREGATION_DIFF",
        source_expression="COUNT(*)",
        target_expression="COUNT(customer_id)",
    )
    assert clf.matches(sig, [sig]) is True
    cand = clf.classify(sig, [sig])
    # Mandatory architectural rule: NULL semantics takes precedence over aggregation semantics
    assert cand.category == DiscrepancyCategory.NULL_SEMANTICS


def test_null_precedence_over_aggregation():
    clf = NullSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="AGGREGATION_DIFF",
        source_expression="COUNT(col IS NULL)",
        target_expression="COUNT(col)",
    )
    assert clf.matches(sig, [sig]) is True


def test_null_does_not_match_normal_filter():
    clf = NullSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="FILTER_DIFF",
        source_expression="amount > 100",
        target_expression="amount >= 100",
    )
    assert clf.matches(sig, [sig]) is False


def test_null_nvl_or_ifnull():
    clf = NullSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="FILTER_DIFF",
        source_expression="NVL(val, 0)",
        target_expression="IFNULL(val, 0)",
    )
    assert clf.matches(sig, [sig]) is True


def test_null_reason_string():
    clf = NullSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="NULL_SEMANTICS_CHANGED",
        source_expression="x IS NULL",
        target_expression="x = NULL",
    )
    cand = clf.classify(sig, [sig])
    assert "NULL handling" in cand.reason_template


def test_null_priority_is_one():
    clf = NullSemanticsClassifier()
    assert clf.priority == 1


def test_null_payload_preservation():
    clf = NullSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="NULL_SEMANTICS_CHANGED",
        payload={"field": "closed_at"},
    )
    cand = clf.classify(sig, [sig])
    assert cand.payload["field"] == "closed_at"
