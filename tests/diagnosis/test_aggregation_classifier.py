"""Unit tests for AggregationClassifier."""

from backend.diagnosis.models import DiscrepancyCategory
from backend.diagnosis.rules.aggregation import AggregationClassifier
from backend.diagnosis.signals import RawDiscrepancySignal


def test_aggregation_classifier_priority():
    clf = AggregationClassifier()
    assert clf.priority == 4
    assert clf.category == DiscrepancyCategory.AGGREGATION_SEMANTICS


def test_aggregation_sum_vs_sum_distinct():
    clf = AggregationClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="AGGREGATION_DIFF",
        source_expression="SUM(amount)",
        target_expression="SUM(DISTINCT amount)",
    )
    assert clf.matches(sig, [sig]) is True
    cand = clf.classify(sig, [sig])
    assert cand.category == DiscrepancyCategory.AGGREGATION_SEMANTICS


def test_aggregation_group_by_changed():
    clf = AggregationClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="AGGREGATION_DIFF",
        source_expression="GROUP BY customer_id",
        target_expression="GROUP BY customer_id, status",
    )
    assert clf.matches(sig, [sig]) is True


def test_aggregation_avg_vs_sum_count():
    clf = AggregationClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="AGGREGATE_MISMATCH",
        source_expression="AVG(amount)",
        target_expression="SUM(amount) / COUNT(amount)",
    )
    assert clf.matches(sig, [sig]) is True


def test_aggregation_having_logic():
    clf = AggregationClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="AGGREGATION_DIFF",
        source_expression="HAVING SUM(amount) > 1000",
        target_expression="HAVING SUM(amount) >= 1000",
    )
    assert clf.matches(sig, [sig]) is True


def test_aggregation_does_not_match_simple_where_filter():
    clf = AggregationClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="FILTER_DIFF",
        source_expression="status = 'ACTIVE'",
        target_expression="status != 'INACTIVE'",
    )
    assert clf.matches(sig, [sig]) is False


def test_aggregation_reason_template():
    clf = AggregationClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="AGGREGATION_DIFF",
        source_expression="SUM(amount)",
        target_expression="SUM(DISTINCT amount)",
    )
    cand = clf.classify(sig, [sig])
    assert "Aggregation logic" in cand.reason_template


def test_aggregation_analysis_path():
    clf = AggregationClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="AGGREGATION_DIFF",
        analysis_path="aggregations[0]",
        source_expression="SUM(amount)",
        target_expression="SUM(DISTINCT amount)",
    )
    cand = clf.classify(sig, [sig])
    assert cand.analysis_path == "aggregations[0]"
