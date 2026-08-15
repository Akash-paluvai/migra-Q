"""Unit tests for JoinSemanticsClassifier."""

from backend.diagnosis.models import DiscrepancyCategory
from backend.diagnosis.rules.join_semantics import JoinSemanticsClassifier
from backend.diagnosis.signals import RawDiscrepancySignal


def test_join_classifier_priority():
    clf = JoinSemanticsClassifier()
    assert clf.priority == 3
    assert clf.category == DiscrepancyCategory.JOIN_SEMANTICS


def test_join_inner_vs_left():
    clf = JoinSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="JOIN_TYPE_CHANGED",
        source_expression="INNER JOIN ON c.id = a.id",
        target_expression="LEFT JOIN ON c.id = a.id",
    )
    assert clf.matches(sig, [sig]) is True
    cand = clf.classify(sig, [sig])
    assert cand.category == DiscrepancyCategory.JOIN_SEMANTICS
    assert cand.subcategory == "JOIN_TYPE_OR_CONDITION_CHANGED"


def test_join_condition_changed():
    clf = JoinSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="JOIN_CONDITION_CHANGED",
        source_expression="JOIN ON c.customer_id = a.customer_id",
        target_expression="JOIN ON c.customer_id = a.account_id",
    )
    assert clf.matches(sig, [sig]) is True


def test_join_type_changed_in_payload():
    clf = JoinSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="RULE_MISMATCH",
        payload={"category": "JOIN_TYPE_CHANGED", "source_value": "INNER", "target_value": "LEFT"},
    )
    assert clf.matches(sig, [sig]) is True


def test_join_left_vs_right():
    clf = JoinSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="JOIN_DIFF",
        source_expression="LEFT JOIN customers",
        target_expression="RIGHT JOIN customers",
    )
    assert clf.matches(sig, [sig]) is True


def test_join_does_not_match_filter():
    clf = JoinSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="FILTER_DIFF",
        source_expression="amount > 100",
        target_expression="amount > 200",
    )
    assert clf.matches(sig, [sig]) is False


def test_join_reason_template():
    clf = JoinSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="JOIN_TYPE_CHANGED",
        source_expression="INNER JOIN",
        target_expression="LEFT JOIN",
    )
    cand = clf.classify(sig, [sig])
    assert "Relational join semantics differ" in cand.reason_template


def test_join_analysis_path_default():
    clf = JoinSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="JOIN_TYPE_CHANGED",
        source_expression="INNER JOIN",
        target_expression="LEFT JOIN",
    )
    cand = clf.classify(sig, [sig])
    assert cand.analysis_path == "joins[0]"


def test_join_priority_is_three():
    clf = JoinSemanticsClassifier()
    assert clf.priority == 3


def test_join_payload_preserved():
    clf = JoinSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="JOIN_TYPE_CHANGED",
        payload={"left_table": "customers", "right_table": "accounts"},
    )
    cand = clf.classify(sig, [sig])
    assert cand.payload["left_table"] == "customers"
