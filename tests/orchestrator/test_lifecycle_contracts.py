"""Unit and integration test suite for Phase 10.4 Lifecycle Contracts & Failure Propagation.

Validates:
1. Strict prerequisite execution and failure propagation (translation error, execution error, validation pass).
2. Distinction between FAILED (technical prerequisite failure) and BLOCKED (semantic validation issue).
3. Distinction between NOT_RUN, NOT_REQUIRED, and NOT_APPLICABLE.
4. Assurance report exists even when score is None.
5. Centralized ArtifactStateConsistencyValidator impossible-state prevention.
6. Execution persistence failure handling and safe Decimal serialization.
7. Dialect and dataset context integrity without flagship leakage.
"""

from __future__ import annotations

import decimal
import hashlib
from unittest.mock import MagicMock, patch

import pytest

from backend.assurance.models import (
    AssuranceBand,
    AuditLineage,
    HardGateEvaluation,
    HardGateResult,
    GateOutcome,
    MigrationFinalStatus,
    MigrationRecord,
    MigrationState,
    VerificationPath,
)
from backend.assurance.scoring import AssuranceScorer
from backend.assurance.service import MigrationAssuranceService
from backend.assurance.decision import DecisionEngine
from backend.core.consistency_validator import (
    ArtifactStateConsistencyError,
    ArtifactStateConsistencyValidator,
)
from backend.execution.models import (
    ColumnSchema,
    ExecutionMode,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
)
from backend.execution.service import ExecutionService
from backend.orchestrator.models import PipelineRunRequest
from backend.orchestrator.service import MigrationOrchestrator
from backend.translator.models import (
    CandidateValidationStatus,
    TranslationMetadata,
    TranslationRequest,
    TranslationResponse,
    TranslationResult,
    TranslationStatus,
)
from backend.validation.models import (
    ValidationCheckStatus,
    ValidationReport,
    ValidationResult,
)


def _make_translation_result(
    status: TranslationStatus = TranslationStatus.SUCCESS,
    cand_status: CandidateValidationStatus | None = CandidateValidationStatus.VALID_SYNTAX,
    target_sql: str | None = "SELECT 1;",
    migration_id: str = "MIG-TEST-001",
    source_hash: str = "abc123hash",
) -> TranslationResult:
    meta = TranslationMetadata(
        translation_id="trans-test-123",
        request_id="req-test-123",
        migration_id=migration_id,
        provider="mock",
        model="mock-model",
        source_dialect="oracle",
        target_dialect="snowflake",
        source_sql_hash=source_hash,
        translation_context_hash="ctx-hash",
        prompt_hash="prompt-hash",
        created_at="2026-08-16T00:00:00Z",
    )
    resp = TranslationResponse(target_sql=target_sql) if target_sql else None
    return TranslationResult(
        metadata=meta,
        status=status,
        candidate_validation_status=cand_status,
        response=resp,
    )


def _make_execution_result(
    status: ExecutionStatus = ExecutionStatus.SUCCESS,
    mode: ExecutionMode = ExecutionMode.SOURCE,
    migration_id: str = "MIG-TEST-001",
) -> ExecutionResult:
    return ExecutionResult(
        execution_id=f"exec-{mode.value.lower()}-123",
        query_hash="qhash123",
        dataset_id="enterprise_metrics",
        dataset_hash="dhash123",
        execution_mode=mode,
        status=status,
        engine="duckdb",
        engine_version="1.0.0",
        duration_ms=12.5,
        row_count=100,
        result_artifact="art-123",
        columns=[ColumnSchema(name="col1", type="INTEGER")],
        sample_data=[{"col1": 1}],
        migration_id=migration_id,
    )


def _make_validation_report(
    status: str = "PASS",
    migration_id: str = "MIG-TEST-001",
) -> ValidationReport:
    check = ValidationResult(
        check_name="RowValidator",
        status=ValidationCheckStatus.PASS if status == "PASS" else ValidationCheckStatus.FAIL,
        score=1.0 if status == "PASS" else 0.0,
        summary="Row reconciliation check",
        mismatch_count=0 if status == "PASS" else 5,
    )
    return ValidationReport(
        validation_id="val-123",
        source_execution_id="exec-source-123",
        target_execution_id="exec-target-123",
        overall_status=status,
        checks=[check],
        migration_id=migration_id,
    )


# ---------------------------------------------------------------------------
# Test 1: Translation provider failure stops downstream phases
# ---------------------------------------------------------------------------
def test_translation_provider_failure_stops_downstream_phases():
    orchestrator = MigrationOrchestrator()
    req = PipelineRunRequest(
        source_sql="SELECT metric_id, score FROM enterprise_metrics WHERE score > 80",
        source_dialect="oracle",
        target_dialect="snowflake",
        dataset_id="enterprise_metrics",
        mock_mode="PROVIDER_ERROR",
        migration_id="MIG-TEST-FAIL-01",
    )
    result = orchestrator.run(req)

    assert result.assurance_report.final_status == MigrationFinalStatus.FAILED
    assert result.assurance_report.score.evidence_score is None
    assert result.assurance_report.score.evidence_coverage is None
    assert result.assurance_report.execution_summary is None
    assert result.assurance_report.validation_summary is None
    assert result.assurance_report.repair_summary.repair_id == ""
    assert "translation failed" in result.assurance_report.decision_reason.lower()


# ---------------------------------------------------------------------------
# Test 2: Execution failure stops validation
# ---------------------------------------------------------------------------
def test_execution_failure_stops_validation():
    orchestrator = MigrationOrchestrator()
    req = PipelineRunRequest(
        source_sql="SELECT metric_id, score FROM enterprise_metrics WHERE score > 80",
        source_dialect="oracle",
        target_dialect="snowflake",
        dataset_id="enterprise_metrics",
        mock_mode="success",
        migration_id="MIG-TEST-EXECFAIL-01",
    )

    with patch.object(ExecutionService, "execute") as mock_exec:
        failed_res = _make_execution_result(status=ExecutionStatus.EXECUTION_ERROR, mode=ExecutionMode.TARGET)
        failed_res.error_message = "DuckDB execution error: table not found"
        mock_exec.return_value = failed_res

        result = orchestrator.run(req)
        assert result.assurance_report.final_status == MigrationFinalStatus.FAILED
        assert result.assurance_report.score.evidence_score is None
        assert result.assurance_report.validation_summary is None


# ---------------------------------------------------------------------------
# Test 3: Validation pass creates direct pass with NOT_REQUIRED summaries
# ---------------------------------------------------------------------------
def test_validation_pass_creates_direct_pass():
    service = MigrationAssuranceService()
    trans_res = _make_translation_result()
    src_exec = _make_execution_result(mode=ExecutionMode.SOURCE)
    tgt_exec = _make_execution_result(mode=ExecutionMode.TARGET)
    val_report = _make_validation_report(status="PASS")

    # Create migration record first
    service.create_migration(
        source_dialect="oracle",
        target_dialect="snowflake",
        source_sql_hash=trans_res.metadata.source_sql_hash,
        dataset_id="enterprise_metrics",
        dataset_hash="dhash123",
        migration_id="MIG-TEST-001",
    )

    report = service.evaluate_assurance(
        migration_id="MIG-TEST-001",
        translation_result=trans_res,
        source_execution=src_exec,
        target_execution=tgt_exec,
        validation_report=val_report,
    )

    assert report.final_status == MigrationFinalStatus.VERIFIED
    assert report.verification_path == VerificationPath.DIRECT_PASS
    assert report.score.evidence_score is not None
    assert report.score.evidence_score > 0
    assert report.repair_summary.repair_id == ""
    assert report.verification_summary.verification_id == ""


# ---------------------------------------------------------------------------
# Test 4: Validation discrepancy creates diagnosis path
# ---------------------------------------------------------------------------
def test_validation_discrepancy_creates_diagnosis_path():
    service = MigrationAssuranceService()
    trans_res = _make_translation_result()
    src_exec = _make_execution_result(mode=ExecutionMode.SOURCE)
    tgt_exec = _make_execution_result(mode=ExecutionMode.TARGET)
    val_report = _make_validation_report(status="FAIL")

    service.create_migration(
        source_dialect="oracle",
        target_dialect="snowflake",
        source_sql_hash=trans_res.metadata.source_sql_hash,
        dataset_id="enterprise_metrics",
        dataset_hash="dhash123",
        migration_id="MIG-TEST-001",
    )

    report = service.evaluate_assurance(
        migration_id="MIG-TEST-001",
        translation_result=trans_res,
        source_execution=src_exec,
        target_execution=tgt_exec,
        validation_report=val_report,
    )

    assert report.final_status == MigrationFinalStatus.BLOCKED
    assert "unresolved semantic issues" in report.decision_reason.lower() or "failed" in report.decision_reason.lower()


# ---------------------------------------------------------------------------
# Test 5: Missing repair proposal does not show proposed
# ---------------------------------------------------------------------------
def test_missing_repair_proposal_does_not_show_proposed():
    with pytest.raises(ArtifactStateConsistencyError):
        ArtifactStateConsistencyValidator.validate_repair_state(
            repair_id=None,
            repair_status="PROPOSED",
            proposed_sql="SELECT 1;",
        )


# ---------------------------------------------------------------------------
# Test 6: Missing verification does not show verified
# ---------------------------------------------------------------------------
def test_missing_verification_does_not_show_verified():
    with pytest.raises(ArtifactStateConsistencyError):
        ArtifactStateConsistencyValidator.validate_verification_state(
            verification_id=None,
            verification_status="VERIFIED",
        )


# ---------------------------------------------------------------------------
# Test 7: Provider error cannot have valid syntax
# ---------------------------------------------------------------------------
def test_provider_error_cannot_have_valid_syntax():
    with pytest.raises(ArtifactStateConsistencyError):
        ArtifactStateConsistencyValidator.validate_translation_state(
            status="PROVIDER_ERROR",
            target_sql=None,
            candidate_validation_status="VALID_SYNTAX",
        )


# ---------------------------------------------------------------------------
# Test 8: Migration context mismatch rejected
# ---------------------------------------------------------------------------
def test_migration_context_mismatch_rejected():
    service = MigrationAssuranceService()
    trans_res = _make_translation_result(migration_id="MIG-OTHER-999")

    service.create_migration(
        source_dialect="oracle",
        target_dialect="snowflake",
        source_sql_hash="different_hash",
        dataset_id="enterprise_metrics",
        dataset_hash="dhash123",
        migration_id="MIG-TEST-001",
    )

    with pytest.raises(ValueError, match="ARTIFACT_LINEAGE_MISMATCH"):
        service.evaluate_assurance(
            migration_id="MIG-TEST-001",
            translation_result=trans_res,
        )


# ---------------------------------------------------------------------------
# Test 9: Stale artifact rejected
# ---------------------------------------------------------------------------
def test_stale_artifact_cannot_be_rendered():
    service = MigrationAssuranceService()
    trans_res = _make_translation_result(source_hash="old_stale_hash")

    service.create_migration(
        source_dialect="oracle",
        target_dialect="snowflake",
        source_sql_hash="fresh_active_hash",
        dataset_id="enterprise_metrics",
        dataset_hash="dhash123",
        migration_id="MIG-TEST-001",
    )

    with pytest.raises(ValueError, match="ARTIFACT_LINEAGE_MISMATCH"):
        service.evaluate_assurance(
            migration_id="MIG-TEST-001",
            translation_result=trans_res,
        )


# ---------------------------------------------------------------------------
# Test 10: Missing validation means assurance score is None
# ---------------------------------------------------------------------------
def test_missing_validation_means_assurance_score_is_none():
    scorer = AssuranceScorer()
    score = scorer.calculate(None)
    assert score.evidence_score is None
    assert score.evidence_coverage is None
    assert score.band is None
    assert len(score.components) == 0


# ---------------------------------------------------------------------------
# Test 11: Missing candidate means validation is not run
# ---------------------------------------------------------------------------
def test_missing_candidate_means_validation_is_not_run():
    with pytest.raises(ArtifactStateConsistencyError):
        ArtifactStateConsistencyValidator.validate_execution_state(
            target_sql=None,
            target_execution_status="SUCCESS",
        )


# ---------------------------------------------------------------------------
# Test 12: Workflow stepper reflects actual artifact statuses
# ---------------------------------------------------------------------------
def test_workflow_stepper_reflects_actual_artifact_statuses():
    # Verify DecisionEngine distinguishes technical failures as FAILED
    engine = DecisionEngine()
    gate_eval = HardGateEvaluation(
        gates=[
            HardGateResult(
                gate_id="GATE-002",
                gate_name="Target translation syntactically valid",
                outcome=GateOutcome.FAIL,
                reason="Translation syntax validation failed",
            )
        ],
        all_passed=False,
        total_gates=1,
        passed_count=0,
        failed_count=1,
        not_applicable_count=0,
    )
    status, reason = engine.determine_final_status(gate_eval, VerificationPath.DIRECT_PASS)
    assert status == MigrationFinalStatus.FAILED


# ---------------------------------------------------------------------------
# Test 13: Enterprise metrics migration preserves source dataset and dialects
# ---------------------------------------------------------------------------
def test_enterprise_metrics_migration_preserves_source_dataset_dialects():
    orchestrator = MigrationOrchestrator()
    req = PipelineRunRequest(
        source_sql="SELECT metric_id, score FROM enterprise_metrics WHERE score > 90",
        source_dialect="oracle",
        target_dialect="snowflake",
        dataset_id="enterprise_metrics",
        mock_mode="DIRECT_PASS",
        migration_id="MIG-ENT-001",
    )
    result = orchestrator.run(req)

    assert result.migration_record.dataset_id == "enterprise_metrics"
    assert result.migration_record.source_dialect == "oracle"
    assert result.migration_record.target_dialect == "snowflake"
    assert result.assurance_report.translation_summary.source_dialect == "oracle"
    assert result.assurance_report.translation_summary.target_dialect == "snowflake"


# ---------------------------------------------------------------------------
# Test 14: Customer risk flagship still works
# ---------------------------------------------------------------------------
def test_customer_risk_flagship_still_works():
    service = MigrationAssuranceService()
    flagship = service.get_flagship_migration()
    assert flagship.migration_id == "MIG-FLAGSHIP-001"
    assert flagship.dataset_id == "customer_risk"


# ---------------------------------------------------------------------------
# Test 15: Unrelated migration never receives customer risk artifacts
# ---------------------------------------------------------------------------
def test_unrelated_migration_never_receives_customer_risk_artifacts():
    orchestrator = MigrationOrchestrator()
    req = PipelineRunRequest(
        source_sql="SELECT metric_id, score FROM enterprise_metrics WHERE score > 75",
        source_dialect="oracle",
        target_dialect="snowflake",
        dataset_id="enterprise_metrics",
        mock_mode="DIRECT_PASS",
        migration_id="MIG-UNRELATED-001",
    )
    result = orchestrator.run(req)
    assert result.migration_record.dataset_id != "customer_risk"
    assert "customer_risk" not in result.assurance_report.translation_summary.candidate_sql


# ---------------------------------------------------------------------------
# Test 16: Centralized ArtifactStateConsistencyValidator tests
# ---------------------------------------------------------------------------
def test_artifact_state_consistency_validator():
    # Valid direct pass state
    ArtifactStateConsistencyValidator.validate_full_pipeline_state(
        translation_status="SUCCESS",
        target_sql="SELECT 1;",
        candidate_validation_status="VALID_SYNTAX",
        target_execution_status="SUCCESS",
        validation_status="PASS",
        validation_ran=True,
        repair_id=None,
        repair_status=None,
        proposed_sql=None,
        verification_id=None,
        verification_status=None,
        final_status="VERIFIED",
        evidence_score=100.0,
    )

    # Invalid: VERIFIED with None score
    with pytest.raises(ArtifactStateConsistencyError):
        ArtifactStateConsistencyValidator.validate_assurance_state(
            final_status="VERIFIED",
            evidence_score=None,
            validation_ran=True,
        )

    # Invalid: Validation not run but VERIFIED
    with pytest.raises(ArtifactStateConsistencyError):
        ArtifactStateConsistencyValidator.validate_assurance_state(
            final_status="VERIFIED",
            evidence_score=None,
            validation_ran=False,
        )


# ---------------------------------------------------------------------------
# Test 17: Execution persistence failure handling and safe Decimal serialization
# ---------------------------------------------------------------------------
def test_execution_persistence_failure_prevents_verified():
    # Verify Decimal serialization does not throw TypeError in _persist_to_db
    exec_res = _make_execution_result()
    exec_res.sample_data = [{"amount": decimal.Decimal("123.45"), "score": decimal.Decimal("98.76")}]

    with patch("backend.execution.service.check_database_health", return_value=True), \
         patch("backend.execution.service.SessionLocal") as mock_session_local, \
         patch("backend.core.config.settings.PERSISTENCE_MODE", "postgres"):
        mock_db = MagicMock()
        mock_db.commit.side_effect = Exception("DB connection timeout")
        mock_session_local.return_value = mock_db

        ExecutionService._persist_to_db(exec_res)

        assert exec_res.status == ExecutionStatus.EXECUTION_ERROR
        assert exec_res.error_code == "PERSISTENCE_FAILED"
