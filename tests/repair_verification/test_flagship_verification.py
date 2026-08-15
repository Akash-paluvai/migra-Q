"""End-to-end flagship repair verification tests for Phase 8."""

from backend.diagnosis.models import DiscrepancyCategory, DiscrepancyRecord, DiscrepancyReport
from backend.diagnosis_ai.models import AIDiagnosis, DiagnosisStatus, RepairProposal, RepairStatus
from backend.execution.models import ExecutionResult, ExecutionStatus
from backend.repair_verification.models import DiscrepancyOutcomeStatus, VerificationStatus
from backend.repair_verification.service import RepairVerificationService
from backend.validation.models import ValidationReport


def test_flagship_boundary_refund_repair_verification(monkeypatch):
    """Flagship scenario: Verifying candidate repair for customer refund boundary discrepancy (10,512 affected rows -> 0 affected rows)."""
    orig_sql = """
SELECT
    c.customer_id,
    c.customer_segment,
    SUM(t.amount) AS total_amount,
    CASE
        WHEN t.amount >= 500
        THEN 'HIGH_RISK'
        ELSE 'NORMAL'
    END AS risk_class
FROM transactions AS t
INNER JOIN customers AS c
    ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;
    """.strip()

    repaired_sql = """
SELECT
    c.customer_id,
    c.customer_segment,
    SUM(t.amount) AS total_amount,
    CASE
        WHEN t.amount > 500
        THEN 'HIGH_RISK'
        ELSE 'NORMAL'
    END AS risk_class
FROM transactions AS t
INNER JOIN customers AS c
    ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;
    """.strip()

    prop = RepairProposal(
        repair_id="rep-flagship-001",
        diagnosis_id="diag-flagship-001",
        discrepancy_id="D-001",
        status=RepairStatus.PROPOSED,
        original_sql=orig_sql,
        proposed_sql=repaired_sql,
        changed_region="columns[risk_class]",
    )
    diag = AIDiagnosis(
        diagnosis_id="diag-flagship-001",
        discrepancy_id="D-001",
        status=DiagnosisStatus.DIAGNOSED,
        observed_change="Shift",
        likely_mechanism="Mechanism",
        possible_cause="Cause",
        uncertainty="None",
    )

    src_exec = ExecutionResult(
        execution_id="exec-flagship-src",
        query_hash="hash-src",
        dataset_id="customer_risk",
        dataset_hash="ds-hash-customer-risk",
        execution_mode="TARGET",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T12:00:00Z",
        row_count=100000,
    )
    tgt_exec_before = ExecutionResult(
        execution_id="exec-flagship-tgt-before",
        query_hash="hash-tgt-before",
        dataset_id="customer_risk",
        dataset_hash="ds-hash-customer-risk",
        execution_mode="TARGET",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T12:00:00Z",
        row_count=100000,
    )
    rep_exec = ExecutionResult(
        execution_id="exec-flagship-tgt-repaired",
        query_hash="hash-tgt-repaired",
        dataset_id="customer_risk",
        dataset_hash="ds-hash-customer-risk",
        execution_mode="TARGET",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T12:00:00Z",
        row_count=100000,
    )

    d_before = DiscrepancyRecord(
        discrepancy_id="D-001",
        validation_id="val-flagship-before",
        category=DiscrepancyCategory.BOUNDARY_CONDITION,
        severity="HIGH",  # type: ignore[arg-type]
        classification_confidence=0.98,
        classification_method="DETERMINISTIC_RULE",  # type: ignore[arg-type]
        classification_reason="Inclusive boundary comparison t.amount >= 500",
        source_expression="t.amount > 500",
        target_expression="t.amount >= 500",
        affected_output_columns=["risk_class"],
        affected_row_count=10512,
        total_output_rows=100000,
        analysis_path="columns[risk_class]",
        created_at="2026-08-15T12:00:00Z",
    )

    val_before = ValidationReport(
        validation_id="val-flagship-before",
        source_execution_id="exec-flagship-src",
        target_execution_id="exec-flagship-tgt-before",
    )
    disc_before = DiscrepancyReport(
        diagnosis_id="diag-flagship-001",
        validation_id="val-flagship-before",
        discrepancies=[d_before],
    )

    val_after = ValidationReport(
        validation_id="val-flagship-after",
        source_execution_id="exec-flagship-src",
        target_execution_id="exec-flagship-tgt-repaired",
    )
    disc_after = DiscrepancyReport(
        diagnosis_id="diag-flagship-after",
        validation_id="val-flagship-after",
        discrepancies=[],
    )

    monkeypatch.setattr("backend.repair_verification.executor.RepairExecutor.execute_repaired_sql", lambda proposed_sql, dataset_id, target_dialect: rep_exec)
    monkeypatch.setattr("backend.validation.orchestrator.ValidationOrchestrator.validate", lambda self, ctx: val_after)
    monkeypatch.setattr("backend.diagnosis.orchestrator.DiagnosisOrchestrator.diagnose", lambda self, report, source_analysis, target_analysis: disc_after)

    result = RepairVerificationService.verify_repair(
        repair_id="rep-flagship-001",
        discrepancy_id="D-001",
        repair_proposal=prop,
        ai_diagnosis=diag,
        validation_report_before=val_before,
        discrepancy_report_before=disc_before,
        source_execution=src_exec,
        target_execution_before=tgt_exec_before,
    )

    # Flagship Verification Acceptance Assertions
    assert result.status == VerificationStatus.VERIFIED
    assert result.affected_rows_before == 10512
    assert result.affected_rows_after == 0
    assert result.reduction_count == 10512
    assert result.reduction_percentage == 100.0
    assert result.remaining_discrepancy_count == 0
    assert result.new_discrepancy_count == 0
    assert result.resolved_discrepancy_count == 1
    assert result.resolved_discrepancies == ["D-001"]

    out = result.outcomes[0]
    assert out.discrepancy_id_before == "D-001"
    assert out.status == DiscrepancyOutcomeStatus.RESOLVED
    assert out.reduction_percentage == 100.0


def test_secondary_scenario_repair_d1_leaves_d2_intact(monkeypatch):
    """Secondary scenario: Discrepancies D-001 and D-002 exist before.

    Repair targets D-001 and resolves it, leaving D-002 untouched.
    Status must be VERIFIED for D-001 (or PARTIALLY_RESOLVED if overall remaining), with D-002 preserved.
    """
    d1_before = DiscrepancyRecord(
        discrepancy_id="D-001",
        validation_id="val-sec-before",
        category=DiscrepancyCategory.BOUNDARY_CONDITION,
        severity="HIGH",  # type: ignore[arg-type]
        classification_confidence=0.98,
        classification_method="DETERMINISTIC_RULE",  # type: ignore[arg-type]
        classification_reason="Inclusive boundary",
        source_expression="t.amount > 500",
        target_expression="t.amount >= 500",
        affected_output_columns=["risk_class"],
        affected_row_count=10512,
        total_output_rows=100000,
        analysis_path="columns[risk_class]",
        created_at="2026-08-15T12:00:00Z",
    )

    d2_before = DiscrepancyRecord(
        discrepancy_id="D-002",
        validation_id="val-sec-before",
        category=DiscrepancyCategory.NULL_SEMANTICS,
        severity="HIGH",  # type: ignore[arg-type]
        classification_confidence=0.95,
        classification_method="DETERMINISTIC_RULE",  # type: ignore[arg-type]
        classification_reason="COUNT(*) vs COUNT(col)",
        source_expression="COUNT(*)",
        target_expression="COUNT(customer_segment)",
        affected_output_columns=["cnt"],
        affected_row_count=200,
        total_output_rows=100000,
        analysis_path="select_projections",
        created_at="2026-08-15T12:00:00Z",
    )

    prop = RepairProposal(
        repair_id="rep-sec-001",
        diagnosis_id="diag-sec-001",
        discrepancy_id="D-001",
        status=RepairStatus.PROPOSED,
        original_sql="SELECT customer_id, refund_amount FROM transactions WHERE refund_amount >= 500;",
        proposed_sql="SELECT customer_id, refund_amount FROM transactions WHERE refund_amount > 500;",
        changed_region="where_clause",
    )
    diag = AIDiagnosis(
        diagnosis_id="diag-sec-001",
        discrepancy_id="D-001",
        status=DiagnosisStatus.DIAGNOSED,
        observed_change="Shift",
        likely_mechanism="Mechanism",
        possible_cause="Cause",
        uncertainty="None",
    )

    src_exec = ExecutionResult(
        execution_id="exec-sec-src",
        query_hash="h1",
        dataset_id="customer_risk",
        dataset_hash="ds-hash",
        execution_mode="TARGET",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T12:00:00Z",
        row_count=100,
    )
    tgt_exec_before = ExecutionResult(
        execution_id="exec-sec-tgt",
        query_hash="h2",
        dataset_id="customer_risk",
        dataset_hash="ds-hash",
        execution_mode="TARGET",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T12:00:00Z",
        row_count=100,
    )
    rep_exec = ExecutionResult(
        execution_id="exec-sec-rep",
        query_hash="h3",
        dataset_id="customer_risk",
        dataset_hash="ds-hash",
        execution_mode="TARGET",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T12:00:00Z",
        row_count=100,
    )

    val_before = ValidationReport(validation_id="val-sec-before", source_execution_id="exec-sec-src", target_execution_id="exec-sec-tgt")
    disc_before = DiscrepancyReport(diagnosis_id="diag-sec-001", validation_id="val-sec-before", discrepancies=[d1_before, d2_before])

    # After repair: D-001 is resolved, but D-002 remains!
    val_after = ValidationReport(validation_id="val-sec-after", source_execution_id="exec-sec-src", target_execution_id="exec-sec-rep")
    disc_after = DiscrepancyReport(diagnosis_id="diag-sec-after", validation_id="val-sec-after", discrepancies=[d2_before])

    monkeypatch.setattr("backend.repair_verification.executor.RepairExecutor.execute_repaired_sql", lambda proposed_sql, dataset_id, target_dialect: rep_exec)
    monkeypatch.setattr("backend.validation.orchestrator.ValidationOrchestrator.validate", lambda self, ctx: val_after)
    monkeypatch.setattr("backend.diagnosis.orchestrator.DiagnosisOrchestrator.diagnose", lambda self, report, source_analysis, target_analysis: disc_after)

    result = RepairVerificationService.verify_repair(
        repair_id="rep-sec-001",
        discrepancy_id="D-001",
        repair_proposal=prop,
        ai_diagnosis=diag,
        validation_report_before=val_before,
        discrepancy_report_before=disc_before,
        source_execution=src_exec,
        target_execution_before=tgt_exec_before,
    )

    # D-001 targeted discrepancy is RESOLVED
    assert result.outcomes[0].status == DiscrepancyOutcomeStatus.RESOLVED
    assert "D-001" in result.resolved_discrepancies
    # Untouched D-002 remains
    assert "D-002" in result.remaining_discrepancies
    assert result.new_discrepancy_count == 0
    assert result.status == VerificationStatus.VERIFIED
