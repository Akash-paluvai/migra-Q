"""Unit tests for diagnosis domain models and contracts."""

from backend.diagnosis.models import (
    ClassificationMethod,
    DiscrepancyCategory,
    DiscrepancyRecord,
    DiscrepancyReport,
    DiscrepancySeverity,
    ImpactMetrics,
    TypedEvidence,
    TypedEvidenceType,
)
from backend.diagnosis.signals import RawDiscrepancySignal


def test_discrepancy_category_enum_values():
    assert DiscrepancyCategory.BOUNDARY_CONDITION.value == "BOUNDARY_CONDITION"
    assert DiscrepancyCategory.NULL_SEMANTICS.value == "NULL_SEMANTICS"
    assert DiscrepancyCategory.JOIN_SEMANTICS.value == "JOIN_SEMANTICS"
    assert DiscrepancyCategory.AGGREGATION_SEMANTICS.value == "AGGREGATION_SEMANTICS"
    assert DiscrepancyCategory.DATE_SEMANTICS.value == "DATE_SEMANTICS"
    assert DiscrepancyCategory.TYPE_CONVERSION.value == "TYPE_CONVERSION"
    assert DiscrepancyCategory.FILTER_LOGIC.value == "FILTER_LOGIC"
    assert DiscrepancyCategory.CASE_LOGIC.value == "CASE_LOGIC"
    assert DiscrepancyCategory.COLUMN_MAPPING.value == "COLUMN_MAPPING"
    assert DiscrepancyCategory.SET_SEMANTICS.value == "SET_SEMANTICS"
    assert DiscrepancyCategory.UNKNOWN.value == "UNKNOWN"


def test_severity_enum():
    assert DiscrepancySeverity.CRITICAL.value == "CRITICAL"
    assert DiscrepancySeverity.HIGH.value == "HIGH"
    assert DiscrepancySeverity.MEDIUM.value == "MEDIUM"
    assert DiscrepancySeverity.LOW.value == "LOW"
    assert DiscrepancySeverity.INFO.value == "INFO"


def test_classification_method_enum():
    assert ClassificationMethod.COMBINED_DETERMINISTIC.value == "COMBINED_DETERMINISTIC"
    assert ClassificationMethod.DETERMINISTIC_RULE.value == "DETERMINISTIC_RULE"
    assert ClassificationMethod.UNKNOWN.value == "UNKNOWN"


def test_raw_discrepancy_signal_schema():
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="RULE_DIFF",
        analysis_path="business_rules[0]",
        source_expression="amount > 500",
        target_expression="amount >= 500",
        payload={"rule_id": "R1"},
    )
    assert sig.source_validator == "BusinessRuleValidator"
    assert sig.signal_type == "RULE_DIFF"
    assert sig.payload["rule_id"] == "R1"


def test_typed_evidence_schema():
    ev = TypedEvidence(
        type=TypedEvidenceType.ROW_DIFF.value,
        column="risk_class",
        value=500.0,
        source_result="NORMAL",
        target_result="HIGH_RISK",
        row_key={"customer_id": "C101"},
        detail="Value mismatch at boundary",
        ordinal=1,
    )
    assert ev.type == "ROW_DIFF"
    assert ev.row_key["customer_id"] == "C101"


def test_impact_metrics_schema():
    impact = ImpactMetrics(
        affected_row_count=229,
        total_output_rows=100000,
        affected_percentage=0.229,
        affected_column_count=1,
    )
    assert impact.affected_row_count == 229
    assert impact.affected_percentage == 0.229


def test_discrepancy_record_schema():
    rec = DiscrepancyRecord(
        discrepancy_id="D-001",
        validation_id="val-1",
        category=DiscrepancyCategory.BOUNDARY_CONDITION,
        severity=DiscrepancySeverity.HIGH,
        classification_confidence=1.0,
        classification_method=ClassificationMethod.COMBINED_DETERMINISTIC,
        classification_reason="Operator changed > to >=",
        created_at="2026-08-15T00:00:00Z",
    )
    assert rec.discrepancy_id == "D-001"
    assert rec.category == DiscrepancyCategory.BOUNDARY_CONDITION


def test_discrepancy_report_schema():
    rep = DiscrepancyReport(
        diagnosis_id="diag-1",
        validation_id="val-1",
        created_at="2026-08-15T00:00:00Z",
        discrepancy_count=1,
        category_counts={"BOUNDARY_CONDITION": 1},
    )
    assert rep.diagnosis_id == "diag-1"
    assert rep.category_counts["BOUNDARY_CONDITION"] == 1


def test_discrepancy_confidence_bounds():
    rec = DiscrepancyRecord(
        discrepancy_id="D-001",
        validation_id="val-1",
        category=DiscrepancyCategory.UNKNOWN,
        severity=DiscrepancySeverity.LOW,
        classification_confidence=0.5,
        classification_method=ClassificationMethod.UNKNOWN,
        classification_reason="Unknown",
        created_at="2026-08-15T00:00:00Z",
    )
    assert 0.0 <= rec.classification_confidence <= 1.0


def test_evidence_type_enum_coverage():
    types = [t.value for t in TypedEvidenceType]
    assert "RULE_DIFF" in types
    assert "ROW_DIFF" in types
    assert "BOUNDARY_CASE" in types
