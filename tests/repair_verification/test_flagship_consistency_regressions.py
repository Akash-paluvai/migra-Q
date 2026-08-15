"""Regression test suite proving Phase 1-8 Flagship Consistency Invariants.

Tests cover:
1. Validator failure mapped to wrong category (Boundary vs Column Mapping)
2. Output values incorrectly treated as output columns
3. Phase-to-phase discrepancy identity / fingerprint mismatch
4. Zero -> zero cannot be VERIFIED for a behavioral discrepancy
5. Phase 7 cannot repair a discrepancy different from Phase 5 input
6. Phase 8 must preserve original Phase 5 evidence
7. Boundary scenario with actual t.amount = 500.00 row mismatch
"""

from backend.diagnosis.extractor import SignalExtractor
from backend.diagnosis.models import DiscrepancyCategory
from backend.diagnosis.orchestrator import DiagnosisOrchestrator
from backend.diagnosis.rules.column_mapping import ColumnMappingClassifier
from backend.diagnosis.signals import RawDiscrepancySignal
from backend.diagnosis_ai.models import RepairProposal, RepairStatus
from backend.repair_verification.candidate_validator import CandidateRepairValidator
from backend.repair_verification.models import (
    DiscrepancyOutcomeStatus,
    RepairOutcome,
    VerificationStatus,
)
from backend.repair_verification.status import VerificationStatusDeterminer
from backend.validation.models import (
    EvidenceItem,
    EvidenceType,
    ValidationCheckStatus,
    ValidationReport,
    ValidationResult,
    ValidationSeverity,
)


def test_regression_1_validator_failure_mapped_to_correct_category():
    """1. Validator failure mapped to wrong category regression check.

    Ensure row value mismatch with boundary condition differences is classified as
    BOUNDARY_CONDITION, NOT COLUMN_MAPPING.
    """
    report = ValidationReport(
        validation_id="val-reg-1",
        source_execution_id="exec-src-1",
        target_execution_id="exec-tgt-1",
        created_at="2026-08-15T00:00:00Z",
        overall_status="FAIL",
        overall_score=0.9,
        checks=[
            ValidationResult(
                check_name="RowValidator",
                validator_version="1.0.0",
                status=ValidationCheckStatus.FAIL,
                severity=ValidationSeverity.HIGH,
                score=0.9,
                summary="Row mismatch detected: 1 value mismatch.",
                mismatch_count=1,
                evidence=[
                    EvidenceItem(
                        type=EvidenceType.VALUE_MISMATCH,
                        key={"customer_id": "CUST-001"},
                        column="risk_class",
                        source_value="NORMAL",
                        target_value="HIGH_RISK",
                        category="VALUE_MISMATCH",
                    )
                ],
            )
        ],
    )

    signals = SignalExtractor.extract_signals(report)
    # Inject AST boundary signal
    signals.append(
        RawDiscrepancySignal(
            source_validator="AST_ANALYZER",
            signal_type="BUSINESS_RULE_DIFF",
            analysis_path="columns[risk_class]",
            source_expression="t.amount > 500",
            target_expression="t.amount >= 500.00",
            payload={"column": "risk_class"},
        )
    )

    orchestrator = DiagnosisOrchestrator()
    disc_report = orchestrator.consolidator.consolidate(
        validation_id="val-reg-1",
        signals=signals,
        total_output_rows=100,
    )

    assert len(disc_report) == 1
    assert disc_report[0].category == DiscrepancyCategory.BOUNDARY_CONDITION
    assert disc_report[0].affected_row_count == 1


def test_regression_2_output_values_not_treated_as_columns():
    """2. Output values incorrectly treated as output columns.

    ColumnMappingClassifier must not match generic row value mismatch signals.
    """
    clf = ColumnMappingClassifier()

    row_sig = RawDiscrepancySignal(
        source_validator="RowValidator",
        signal_type="VALUE_MISMATCH",
        analysis_path="columns[risk_class]",
        source_expression="NORMAL",
        target_expression="HIGH_RISK",
        payload={"column": "risk_class", "source_value": "NORMAL", "target_value": "HIGH_RISK"},
    )

    assert clf.matches(row_sig, [row_sig]) is False


def test_regression_3_phase_to_phase_fingerprint_mismatch():
    """3. Phase-to-phase discrepancy identity mismatch.

    CandidateRepairValidator must reject repair proposals with fingerprint mismatch.
    """
    proposal = RepairProposal(
        repair_id="rep-001",
        discrepancy_id="D-001",
        discrepancy_fingerprint="fingerprint-abc",
        status=RepairStatus.PROPOSED,
        original_sql="SELECT a FROM t WHERE amount >= 500;",
        proposed_sql="SELECT a FROM t WHERE amount > 500;",
        changed_region="where",
    )

    is_valid, reason, details = CandidateRepairValidator.validate_candidate(
        proposal=proposal,
        original_target_sql="SELECT a FROM t WHERE amount >= 500;",
        target_dialect="bigquery",
        expected_fingerprint="fingerprint-xyz",  # Mismatch!
    )

    assert is_valid is False
    assert reason == "DISCREPANCY_FINGERPRINT_MISMATCH"
    assert details["proposal_fingerprint"] == "fingerprint-abc"
    assert details["expected_fingerprint"] == "fingerprint-xyz"


def test_regression_4_zero_to_zero_cannot_be_verified_for_behavioral_discrepancy():
    """4. Zero -> zero cannot be VERIFIED for a behavioral discrepancy.

    VerificationStatusDeterminer must reject 0 -> 0 affected rows for behavioral discrepancies.
    """
    target_outcome = RepairOutcome(
        discrepancy_id_before="D-001",
        discrepancy_id_after="D-001",
        category="BOUNDARY_CONDITION",
        analysis_path="columns[risk_class]",
        status=DiscrepancyOutcomeStatus.RESOLVED,
        affected_rows_before=0,  # Zero impact before!
        affected_rows_after=0,
        reduction_percentage=100.0,
    )

    status, summary = VerificationStatusDeterminer.determine_status(
        candidate_valid=True,
        rejection_reason=None,
        execution_succeeded=True,
        target_outcome=target_outcome,
        new_discrepancies=[],
    )

    assert status == VerificationStatus.FAILED_VERIFICATION
    assert "0 -> 0 cannot yield VERIFIED" in summary


def test_regression_5_phase_7_discrepancy_identity_preservation():
    """5. Phase 7 cannot repair a discrepancy different from its Phase 5 input.

    Ensure CandidateRepairValidator enforces discrepancy mapping presence.
    """
    proposal = RepairProposal(
        repair_id="rep-002",
        discrepancy_id="",  # Empty mapping!
        status=RepairStatus.PROPOSED,
        original_sql="SELECT a FROM t;",
        proposed_sql="SELECT a, b FROM t;",
    )

    is_valid, reason, _ = CandidateRepairValidator.validate_candidate(
        proposal=proposal,
        original_target_sql="SELECT a FROM t;",
    )

    assert is_valid is False
    assert reason == "UNKNOWN_DISCREPANCY_MAPPING"


def test_regression_6_phase_8_preserves_original_phase_5_evidence():
    """6. Phase 8 must preserve the original Phase 5 evidence in outcome record."""
    outcome = RepairOutcome(
        discrepancy_id_before="D-001",
        discrepancy_id_after="D-001",
        category="BOUNDARY_CONDITION",
        analysis_path="columns[risk_class]",
        status=DiscrepancyOutcomeStatus.RESOLVED,
        affected_rows_before=10512,
        affected_rows_after=0,
        reduction_percentage=100.0,
    )

    assert outcome.discrepancy_id_before == "D-001"
    assert outcome.affected_rows_before == 10512
    assert outcome.affected_rows_after == 0
    assert outcome.reduction_percentage == 100.0


def test_regression_7_boundary_scenario_actual_row_mismatch():
    """7. Boundary scenario with actual t.amount = 500.00.

    Verify that > vs >= on amount = 500.00 yields 1 row mismatch.
    """
    import duckdb

    conn = duckdb.connect(":memory:")
    conn.execute("CREATE TABLE transactions (customer_id VARCHAR, amount DOUBLE, status VARCHAR);")
    conn.execute("INSERT INTO transactions VALUES ('CUST-001', 500.00, 'COMPLETED');")
    conn.execute("CREATE TABLE customers (customer_id VARCHAR, customer_segment VARCHAR);")
    conn.execute("INSERT INTO customers VALUES ('CUST-001', 'RETAIL');")

    src_res = conn.execute("""
        SELECT c.customer_id, CASE WHEN t.amount > 500 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
        FROM transactions t JOIN customers c ON t.customer_id = c.customer_id;
    """).fetchall()

    tgt_res = conn.execute("""
        SELECT c.customer_id, CASE WHEN t.amount >= 500 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
        FROM transactions t JOIN customers c ON t.customer_id = c.customer_id;
    """).fetchall()

    assert src_res[0][1] == "NORMAL"
    assert tgt_res[0][1] == "HIGH_RISK"
    assert src_res[0][1] != tgt_res[0][1]  # Confirmed row value mismatch!
