"""Unit tests for dataset and validation configuration immutability enforcement."""

import pytest

from backend.diagnosis_ai.models import AIDiagnosis, DiagnosisStatus, RepairProposal, RepairStatus
from backend.execution.models import ExecutionResult, ExecutionStatus
from backend.repair_verification.comparator import DiscrepancyComparator
from backend.repair_verification.context import RepairVerificationContext
from backend.repair_verification.exceptions import ImmutabilityViolationError
from backend.repair_verification.models import RepairOutcome, VerificationStatus
from backend.repair_verification.status import VerificationStatusDeterminer
from backend.validation.models import ValidationReport


def test_dataset_hash_immutability_pass():
    src_exec = ExecutionResult(
        execution_id="exec-src",
        query_hash="q1",
        dataset_id="ds1",
        dataset_hash="hash-123456",
        execution_mode="TARGET",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T12:00:00Z",
        row_count=100,
    )
    rep_exec = ExecutionResult(
        execution_id="exec-rep",
        query_hash="q2",
        dataset_id="ds1",
        dataset_hash="hash-123456",
        execution_mode="TARGET",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T12:00:00Z",
        row_count=100,
    )

    prop = RepairProposal(
        repair_id="rep-1",
        discrepancy_id="D-1",
        status=RepairStatus.PROPOSED,
        original_sql="SELECT 1;",
        proposed_sql="SELECT 2;",
    )
    diag = AIDiagnosis(
        diagnosis_id="diag-1",
        discrepancy_id="D-1",
        status=DiagnosisStatus.DIAGNOSED,
        observed_change="Change",
        likely_mechanism="Mechanism",
        possible_cause="Cause",
        uncertainty="None",
    )
    val_before = ValidationReport(validation_id="val-1", source_execution_id="exec-src", target_execution_id="exec-tgt")

    ctx = RepairVerificationContext(
        repair_proposal=prop,
        ai_diagnosis=diag,
        source_execution=src_exec,
        target_execution_before=src_exec,
        validation_report_before=val_before,
        discrepancy_report_before=None,  # type: ignore[arg-type]
        target_execution_repaired=rep_exec,
    )

    # Must not raise
    DiscrepancyComparator.verify_immutability(ctx)


def test_dataset_hash_immutability_violation_raises():
    src_exec = ExecutionResult(
        execution_id="exec-src",
        query_hash="q1",
        dataset_id="ds1",
        dataset_hash="hash-ORIGINAL",
        execution_mode="TARGET",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T12:00:00Z",
        row_count=100,
    )
    rep_exec = ExecutionResult(
        execution_id="exec-rep",
        query_hash="q2",
        dataset_id="ds1",
        dataset_hash="hash-MUTATED_DATASET",
        execution_mode="TARGET",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T12:00:00Z",
        row_count=100,
    )

    prop = RepairProposal(
        repair_id="rep-1",
        discrepancy_id="D-1",
        status=RepairStatus.PROPOSED,
        original_sql="SELECT 1;",
        proposed_sql="SELECT 2;",
    )
    diag = AIDiagnosis(
        diagnosis_id="diag-1",
        discrepancy_id="D-1",
        status=DiagnosisStatus.DIAGNOSED,
        observed_change="Change",
        likely_mechanism="Mechanism",
        possible_cause="Cause",
        uncertainty="None",
    )
    val_before = ValidationReport(validation_id="val-1", source_execution_id="exec-src", target_execution_id="exec-tgt")

    ctx = RepairVerificationContext(
        repair_proposal=prop,
        ai_diagnosis=diag,
        source_execution=src_exec,
        target_execution_before=src_exec,
        validation_report_before=val_before,
        discrepancy_report_before=None,  # type: ignore[arg-type]
        target_execution_repaired=rep_exec,
    )

    with pytest.raises(ImmutabilityViolationError) as exc_info:
        DiscrepancyComparator.verify_immutability(ctx)

    assert "DATASET_CHANGED" in str(exc_info.value)


def test_status_determiner_fails_on_dataset_change():
    status, summary = VerificationStatusDeterminer.determine_status(
        candidate_valid=True,
        rejection_reason=None,
        execution_succeeded=True,
        target_outcome=RepairOutcome(discrepancy_id_before="D-001", status="RESOLVED"),  # type: ignore[arg-type]
        new_discrepancies=[],
        dataset_unchanged=False,
        immutability_error="DATASET_CHANGED",
    )
    assert status == VerificationStatus.FAILED_VERIFICATION
    assert "Dataset hash changed" in summary


def test_status_determiner_fails_on_config_change():
    status, summary = VerificationStatusDeterminer.determine_status(
        candidate_valid=True,
        rejection_reason=None,
        execution_succeeded=True,
        target_outcome=RepairOutcome(discrepancy_id_before="D-001", status="RESOLVED"),  # type: ignore[arg-type]
        new_discrepancies=[],
        config_unchanged=False,
        immutability_error="VALIDATION_CONFIGURATION_CHANGED",
    )
    assert status == VerificationStatus.FAILED_VERIFICATION
    assert "Validation configuration changed" in summary
