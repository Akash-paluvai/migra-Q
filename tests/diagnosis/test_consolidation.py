"""Unit tests for EvidenceConsolidator and SignalExtractor."""

from backend.diagnosis.evidence import EvidenceConsolidator
from backend.diagnosis.extractor import SignalExtractor
from backend.diagnosis.models import DiscrepancyCategory
from backend.diagnosis.signals import RawDiscrepancySignal
from backend.validation.models import (
    EvidenceItem,
    EvidenceType,
    ValidationCheckStatus,
    ValidationReport,
    ValidationResult,
)


def make_report_with_checks(checks):
    return ValidationReport(
        validation_id="val-101",
        source_execution_id="exec-1",
        target_execution_id="exec-2",
        dataset_id="dev",
        created_at="2026-08-15T00:00:00Z",
        overall_status="FAIL",
        checks=checks,
    )


def test_signal_extraction_from_validation_report():
    checks = [
        ValidationResult(
            check_name="BusinessRuleValidator",
            status=ValidationCheckStatus.FAIL,
            score=0.5,
            summary="Operator mismatch",
            mismatch_count=1,
            evidence=[
                EvidenceItem(
                    type=EvidenceType.RULE_MISMATCH,
                    category="OPERATOR_CHANGED",
                    source_value="amount > 500",
                    target_value="amount >= 500",
                    detail="Operator > vs >=",
                )
            ],
        )
    ]
    report = make_report_with_checks(checks)
    signals = SignalExtractor.extract_signals(report)
    assert len(signals) >= 1
    assert signals[0].source_validator == "BusinessRuleValidator"
    assert signals[0].source_expression == "amount > 500"


def test_consolidation_merges_rule_and_row_signals_into_one_discrepancy():
    rule_sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        analysis_path="business_rules[0].condition.operator",
        source_expression="amount > 500",
        target_expression="amount >= 500",
        payload={"category": "OPERATOR_CHANGED", "source_value": ">", "target_value": ">="},
    )
    row_sig = RawDiscrepancySignal(
        source_validator="RowValidator",
        signal_type="VALUE_MISMATCH",
        analysis_path="business_rules[0].condition.operator",
        source_expression="amount > 500",
        target_expression="amount >= 500",
        payload={
            "mismatch_count": 229,
            "column": "risk_class",
            "source_value": "NORMAL",
            "target_value": "HIGH_RISK",
            "key": {"customer_id": "C18291"},
        },
    )
    edge_sig = RawDiscrepancySignal(
        source_validator="EdgeCaseValidator",
        signal_type="BOUNDARY_CASE",
        analysis_path="business_rules[0].condition.operator",
        source_expression="amount > 500",
        target_expression="amount >= 500",
        payload={"detail": "Boundary scenario failed at 500.00"},
    )

    consolidator = EvidenceConsolidator()
    discrepancies = consolidator.consolidate(
        "val-101", [rule_sig, row_sig, edge_sig], total_output_rows=128430
    )

    # Architectural requirement: Must produce 1 consolidated DiscrepancyRecord (D-001)
    assert len(discrepancies) == 1
    disc = discrepancies[0]
    assert disc.discrepancy_id == "D-001"
    assert disc.category == DiscrepancyCategory.BOUNDARY_CONDITION
    assert disc.affected_row_count == 229
    assert len(disc.validator_checks) == 3
    assert "BusinessRuleValidator" in disc.validator_checks
    assert "RowValidator" in disc.validator_checks
    assert "EdgeCaseValidator" in disc.validator_checks


def test_consolidation_evidence_limit():
    signals = [
        RawDiscrepancySignal(
            source_validator="RowValidator",
            signal_type="VALUE_MISMATCH",
            analysis_path="business_rules[0]",
            source_expression="amount > 500",
            target_expression="amount >= 500",
            payload={
                "mismatch_count": 500,
                "column": f"col_{i}",
                "source_value": "A",
                "target_value": "B",
            },
        )
        for i in range(150)
    ]
    consolidator = EvidenceConsolidator()
    discrepancies = consolidator.consolidate("val-101", signals, max_evidence_items=100)
    assert len(discrepancies) == 1
    assert len(discrepancies[0].evidence) == 100
