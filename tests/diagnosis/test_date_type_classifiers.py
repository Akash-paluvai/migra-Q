"""Unit tests for DateSemanticsClassifier and TypeConversionClassifier."""

from backend.diagnosis.models import DiscrepancyCategory
from backend.diagnosis.rules.date_semantics import DateSemanticsClassifier
from backend.diagnosis.rules.type_conversion import TypeConversionClassifier
from backend.diagnosis.signals import RawDiscrepancySignal


def test_date_semantics_priority():
    clf = DateSemanticsClassifier()
    assert clf.priority == 5
    assert clf.category == DiscrepancyCategory.DATE_SEMANTICS


def test_date_trunc_month_vs_day():
    clf = DateSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="FILTER_DIFF",
        source_expression="DATE_TRUNC('month', created_at)",
        target_expression="DATE_TRUNC('day', created_at)",
    )
    assert clf.matches(sig, [sig]) is True
    cand = clf.classify(sig, [sig])
    assert cand.category == DiscrepancyCategory.DATE_SEMANTICS


def test_date_extract_year():
    clf = DateSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="FILTER_DIFF",
        source_expression="EXTRACT(YEAR FROM created_at)",
        target_expression="YEAR(created_at)",
    )
    assert clf.matches(sig, [sig]) is True


def test_type_conversion_priority():
    clf = TypeConversionClassifier()
    assert clf.priority == 6
    assert clf.category == DiscrepancyCategory.TYPE_CONVERSION


def test_type_conversion_cast_varchar_to_integer():
    clf = TypeConversionClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="TYPE_DIFF",
        source_expression="CAST(customer_id AS VARCHAR)",
        target_expression="CAST(customer_id AS INTEGER)",
    )
    assert clf.matches(sig, [sig]) is True
    cand = clf.classify(sig, [sig])
    assert cand.category == DiscrepancyCategory.TYPE_CONVERSION


def test_type_conversion_schema_type_changed():
    clf = TypeConversionClassifier()
    sig = RawDiscrepancySignal(
        source_validator="SchemaValidator",
        signal_type="SCHEMA_TYPE_CHANGED",
        source_expression="BIGINT",
        target_expression="DOUBLE",
    )
    assert clf.matches(sig, [sig]) is True


def test_date_reason_template():
    clf = DateSemanticsClassifier()
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="FILTER_DIFF",
        source_expression="DATE_TRUNC('month', ts)",
        target_expression="DATE_TRUNC('day', ts)",
    )
    cand = clf.classify(sig, [sig])
    assert "Date/time evaluation semantics differ" in cand.reason_template


def test_type_conversion_reason_template():
    clf = TypeConversionClassifier()
    sig = RawDiscrepancySignal(
        source_validator="SchemaValidator",
        signal_type="SCHEMA_TYPE_CHANGED",
        source_expression="VARCHAR",
        target_expression="INTEGER",
    )
    cand = clf.classify(sig, [sig])
    assert "Data type casting or representation differs" in cand.reason_template
