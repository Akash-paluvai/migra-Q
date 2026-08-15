"""Reproducibility tests and 10 mandatory architectural requirement tests for Phase 5."""

from backend.diagnosis.evidence import EvidenceConsolidator
from backend.diagnosis.models import DiscrepancyCategory, DiscrepancySeverity
from backend.diagnosis.orchestrator import DiagnosisOrchestrator
from backend.diagnosis.signals import RawDiscrepancySignal
from backend.validation.models import (
    EvidenceItem,
    EvidenceType,
    ValidationCheckStatus,
    ValidationReport,
    ValidationResult,
)


def make_report(checks):
    return ValidationReport(
        validation_id="val-test",
        source_execution_id="exec-s",
        target_execution_id="exec-t",
        dataset_id="dev",
        created_at="2026-08-15T00:00:00Z",
        overall_status="FAIL",
        checks=checks,
    )


def test_1_same_rule_difference_different_evidence_one_discrepancy():
    # Same rule diff + different row evidence -> 1 consolidated discrepancy
    sig1 = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        analysis_path="business_rules[0]",
        source_expression="amount > 500",
        target_expression="amount >= 500",
    )
    sig2 = RawDiscrepancySignal(
        source_validator="RowValidator",
        signal_type="VALUE_MISMATCH",
        analysis_path="business_rules[0]",
        source_expression="amount > 500",
        target_expression="amount >= 500",
        payload={
            "column": "risk",
            "source_value": "NORMAL",
            "target_value": "HIGH_RISK",
            "mismatch_count": 50,
        },
    )
    sig3 = RawDiscrepancySignal(
        source_validator="RowValidator",
        signal_type="VALUE_MISMATCH",
        analysis_path="business_rules[0]",
        source_expression="amount > 500",
        target_expression="amount >= 500",
        payload={
            "column": "amount",
            "source_value": 500.0,
            "target_value": 500.0,
            "mismatch_count": 50,
        },
    )

    consolidator = EvidenceConsolidator()
    discrepancies = consolidator.consolidate("val-test", [sig1, sig2, sig3], total_output_rows=1000)
    assert len(discrepancies) == 1
    assert discrepancies[0].discrepancy_id == "D-001"


def test_2_different_rules_same_affected_rows_two_discrepancies():
    # Different rules + same affected rows -> 2 distinct discrepancies
    sig1 = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        analysis_path="business_rules[0]",
        source_expression="amount > 500",
        target_expression="amount >= 500",
    )
    sig2 = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="JOIN_TYPE_CHANGED",
        analysis_path="joins[0]",
        source_expression="INNER JOIN",
        target_expression="LEFT JOIN",
    )

    consolidator = EvidenceConsolidator()
    discrepancies = consolidator.consolidate("val-test", [sig1, sig2], total_output_rows=1000)
    assert len(discrepancies) == 2
    cats = [d.category for d in discrepancies]
    assert DiscrepancyCategory.BOUNDARY_CONDITION in cats
    assert DiscrepancyCategory.JOIN_SEMANTICS in cats


def test_3_structural_difference_zero_affected_rows_lower_severity():
    # Structural diff with 0 affected rows -> LOW severity
    sig = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        analysis_path="business_rules[0]",
        source_expression="amount > 500",
        target_expression="amount >= 500",
    )
    consolidator = EvidenceConsolidator()
    disc_zero = consolidator.consolidate("val-test", [sig], total_output_rows=1000)[0]

    sig_affected = RawDiscrepancySignal(
        source_validator="RowValidator",
        signal_type="VALUE_MISMATCH",
        analysis_path="business_rules[0]",
        source_expression="amount > 500",
        target_expression="amount >= 500",
        payload={"mismatch_count": 300},
    )
    disc_affected = consolidator.consolidate(
        "val-test", [sig, sig_affected], total_output_rows=1000
    )[0]

    assert disc_zero.severity in (DiscrepancySeverity.LOW, DiscrepancySeverity.INFO)
    assert disc_affected.severity in (DiscrepancySeverity.HIGH, DiscrepancySeverity.CRITICAL)


def test_4_structural_difference_plus_affected_rows_higher_confidence():
    # Structural diff only (0.85) vs Structural + execution (0.95)
    sig_struct = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        analysis_path="business_rules[0]",
        source_expression="amount > 500",
        target_expression="amount >= 500",
    )
    consolidator = EvidenceConsolidator()
    disc_struct_only = consolidator.consolidate("val-test", [sig_struct], total_output_rows=1000)[0]

    sig_row = RawDiscrepancySignal(
        source_validator="RowValidator",
        signal_type="VALUE_MISMATCH",
        analysis_path="business_rules[0]",
        source_expression="amount > 500",
        target_expression="amount >= 500",
        payload={"mismatch_count": 50},
    )
    disc_combined = consolidator.consolidate(
        "val-test", [sig_struct, sig_row], total_output_rows=1000
    )[0]

    assert disc_struct_only.classification_confidence == 0.85
    assert disc_combined.classification_confidence == 0.95


def test_5_validator_execution_order_independence():
    # Same signals in different validator order -> identical final DiscrepancyRecord
    sig1 = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        analysis_path="business_rules[0]",
        source_expression="amount > 500",
        target_expression="amount >= 500",
    )
    sig2 = RawDiscrepancySignal(
        source_validator="RowValidator",
        signal_type="VALUE_MISMATCH",
        analysis_path="business_rules[0]",
        source_expression="amount > 500",
        target_expression="amount >= 500",
        payload={"mismatch_count": 100},
    )

    consolidator = EvidenceConsolidator()
    res1 = consolidator.consolidate("val-test", [sig1, sig2], total_output_rows=1000)[0]
    res2 = consolidator.consolidate("val-test", [sig2, sig1], total_output_rows=1000)[0]

    print("RES1:", res1)
    print("RES2:", res2)
    assert res1.category == res2.category
    assert res1.severity == res2.severity
    assert res1.classification_confidence == res2.classification_confidence
    assert res1.discrepancy_signature == res2.discrepancy_signature


def test_6_shuffled_evidence_order_identical_report():
    # Evidence order shuffled -> identical report signature and categories
    checks = [
        ValidationResult(
            check_name="RowValidator",
            status=ValidationCheckStatus.FAIL,
            score=0.1,
            summary="Rows differ",
            evidence=[
                EvidenceItem(type=EvidenceType.ROW_MISMATCH, column="c1", detail="d1"),
                EvidenceItem(type=EvidenceType.ROW_MISMATCH, column="c2", detail="d2"),
            ],
        )
    ]
    report = make_report(checks)

    orchestrator = DiagnosisOrchestrator()
    r1 = orchestrator.diagnose(report)

    # Shuffle checks/evidence
    checks_shuffled = [
        ValidationResult(
            check_name="RowValidator",
            status=ValidationCheckStatus.FAIL,
            score=0.1,
            summary="Rows differ",
            evidence=[
                EvidenceItem(type=EvidenceType.ROW_MISMATCH, column="c2", detail="d2"),
                EvidenceItem(type=EvidenceType.ROW_MISMATCH, column="c1", detail="d1"),
            ],
        )
    ]
    report_shuffled = make_report(checks_shuffled)
    r2 = orchestrator.diagnose(report_shuffled)

    assert r1.discrepancy_count == r2.discrepancy_count
    assert r1.category_counts == r2.category_counts


def test_7_two_unrelated_discrepancies_overlapping_rows_remain_separate():
    sig1 = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        analysis_path="business_rules[0]",
        source_expression="amount > 500",
        target_expression="amount >= 500",
    )
    sig2 = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="NULL_SEMANTICS_CHANGED",
        analysis_path="filters[0]",
        source_expression="closed_at IS NULL",
        target_expression="closed_at = NULL",
    )

    consolidator = EvidenceConsolidator()
    res = consolidator.consolidate("val-test", [sig1, sig2], total_output_rows=1000)
    assert len(res) == 2


def test_8_unknown_syntax_classified_as_unknown():
    sig = RawDiscrepancySignal(
        source_validator="UnknownParser",
        signal_type="UNSUPPORTED_SYNTAX",
        source_expression="CUSTOM_UNSUPPORTED_OPERATOR(a)",
        target_expression="CUSTOM_UNSUPPORTED_OPERATOR(b)",
    )
    consolidator = EvidenceConsolidator()
    res = consolidator.consolidate("val-test", [sig], total_output_rows=1000)
    assert len(res) == 1
    assert res[0].category == DiscrepancyCategory.UNKNOWN


def test_9_unsupported_phase1_analysis_unknown_fallback():
    sig = RawDiscrepancySignal(
        source_validator="AST_ANALYZER",
        signal_type="UNSUPPORTED_AST_FEATURE",
        source_expression="UNSUPPORTED_EXPR",
        target_expression="UNSUPPORTED_EXPR_2",
    )
    consolidator = EvidenceConsolidator()
    res = consolidator.consolidate("val-test", [sig], total_output_rows=1000)
    assert len(res) == 1
    assert res[0].category == DiscrepancyCategory.UNKNOWN


def test_10_rerunning_diagnosis_reproducibility():
    checks = [
        ValidationResult(
            check_name="BusinessRuleValidator",
            status=ValidationCheckStatus.FAIL,
            score=0.5,
            summary="Rule fail",
            evidence=[
                EvidenceItem(
                    type=EvidenceType.RULE_MISMATCH,
                    category="OPERATOR_CHANGED",
                    source_value="amount > 500",
                    target_value="amount >= 500",
                )
            ],
        )
    ]
    report = make_report(checks)
    orchestrator = DiagnosisOrchestrator()

    r1 = orchestrator.diagnose(report)
    r2 = orchestrator.diagnose(report)

    assert r1.discrepancy_count == r2.discrepancy_count
    assert r1.category_counts == r2.category_counts
    assert r1.discrepancies[0].discrepancy_signature == r2.discrepancies[0].discrepancy_signature
    assert r1.discrepancies[0].category == r2.discrepancies[0].category
    assert r1.discrepancies[0].severity == r2.discrepancies[0].severity
    assert (
        r1.discrepancies[0].classification_confidence
        == r2.discrepancies[0].classification_confidence
    )
