"""Unit tests verifying deterministic reproducibility across repeated repair verification runs."""

from backend.diagnosis.models import DiscrepancyCategory, DiscrepancyRecord, DiscrepancyReport
from backend.diagnosis_ai.models import AIDiagnosis, DiagnosisStatus, RepairProposal, RepairStatus
from backend.execution.models import ExecutionResult, ExecutionStatus
from backend.repair_verification.models import VerificationStatus
from backend.repair_verification.service import RepairVerificationService
from backend.validation.models import ValidationReport


def test_repeated_verification_reproducibility(monkeypatch):
    """Verify that repeated verification runs for identical inputs yield identical status, discrepancy counts, and reduction percentages."""
    prop = RepairProposal(
        repair_id="rep-repro-001",
        diagnosis_id="diag-repro-001",
        discrepancy_id="D-001",
        status=RepairStatus.PROPOSED,
        original_sql="SELECT * FROM t WHERE val >= 500;",
        proposed_sql="SELECT * FROM t WHERE val > 500;",
        changed_region="where_clause",
    )
    diag = AIDiagnosis(
        diagnosis_id="diag-repro-001",
        discrepancy_id="D-001",
        status=DiagnosisStatus.DIAGNOSED,
        observed_change="Shift",
        likely_mechanism="Mechanism",
        possible_cause="Cause",
        uncertainty="None",
    )

    src_exec = ExecutionResult(
        execution_id="exec-src-repro",
        query_hash="q1",
        dataset_id="customer_risk",
        dataset_hash="hash-fixed",
        execution_mode="TARGET",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T12:00:00Z",
        row_count=100,
    )
    tgt_exec_before = ExecutionResult(
        execution_id="exec-tgt-repro",
        query_hash="q2",
        dataset_id="customer_risk",
        dataset_hash="hash-fixed",
        execution_mode="TARGET",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T12:00:00Z",
        row_count=100,
    )

    d_before = DiscrepancyRecord(
        discrepancy_id="D-001",
        validation_id="val-repro",
        category=DiscrepancyCategory.BOUNDARY_CONDITION,
        severity="HIGH",  # type: ignore[arg-type]
        classification_confidence=1.0,
        classification_method="DETERMINISTIC_RULE",  # type: ignore[arg-type]
        classification_reason="Boundary",
        affected_row_count=10512,
        total_output_rows=10512,
        created_at="2026-08-15T12:00:00Z",
    )
    val_before = ValidationReport(validation_id="val-repro", source_execution_id="exec-src-repro", target_execution_id="exec-tgt-repro")
    disc_before = DiscrepancyReport(diagnosis_id="diag-repro-001", validation_id="val-repro", discrepancies=[d_before])

    rep_exec = ExecutionResult(
        execution_id="exec-rep-repro",
        query_hash="q3",
        dataset_id="customer_risk",
        dataset_hash="hash-fixed",
        execution_mode="TARGET",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T12:00:00Z",
        row_count=100,
    )
    val_after = ValidationReport(validation_id="val-repro-after", source_execution_id="exec-src-repro", target_execution_id="exec-rep-repro")
    disc_after = DiscrepancyReport(diagnosis_id="diag-after-repro", validation_id="val-repro-after", discrepancies=[])

    monkeypatch.setattr("backend.repair_verification.executor.RepairExecutor.execute_repaired_sql", lambda proposed_sql, dataset_id, target_dialect: rep_exec)
    monkeypatch.setattr("backend.validation.orchestrator.ValidationOrchestrator.validate", lambda self, ctx: val_after)
    monkeypatch.setattr("backend.diagnosis.orchestrator.DiagnosisOrchestrator.diagnose", lambda self, report, source_analysis, target_analysis: disc_after)

    res1 = RepairVerificationService.verify_repair(
        repair_id="rep-repro-001",
        discrepancy_id="D-001",
        repair_proposal=prop,
        ai_diagnosis=diag,
        validation_report_before=val_before,
        discrepancy_report_before=disc_before,
        source_execution=src_exec,
        target_execution_before=tgt_exec_before,
    )

    res2 = RepairVerificationService.verify_repair(
        repair_id="rep-repro-001",
        discrepancy_id="D-001",
        repair_proposal=prop,
        ai_diagnosis=diag,
        validation_report_before=val_before,
        discrepancy_report_before=disc_before,
        source_execution=src_exec,
        target_execution_before=tgt_exec_before,
    )

    # Deterministic comparisons (excluding random verification IDs & duration ms)
    assert res1.status == res2.status == VerificationStatus.VERIFIED
    assert res1.affected_rows_before == res2.affected_rows_before == 10512
    assert res1.affected_rows_after == res2.affected_rows_after == 0
    assert res1.reduction_percentage == res2.reduction_percentage == 100.0
    assert res1.new_discrepancy_count == res2.new_discrepancy_count == 0
    assert res1.remaining_discrepancy_count == res2.remaining_discrepancy_count == 0
    assert res1.resolved_discrepancies == res2.resolved_discrepancies == ["D-001"]
