import pytest
from backend.assurance.service import MigrationAssuranceService, create_candidate_version, get_active_candidate, save_candidate
from backend.core.consistency_validator import CandidateStateError
from backend.orchestrator.service import MigrationOrchestrator
from backend.api.assurance import execute_migration
from fastapi import HTTPException
from backend.execution.service import ExecutionService
from backend.execution.models import ExecutionResult, ExecutionStatus
from backend.validation.service import ValidationService
from backend.validation.models import ValidationReport
from backend.assurance.scoring import AssuranceScorer, AssuranceScore

from backend.assurance.models import PreflightSummary

def test_candidate_execution_uses_active_sql(monkeypatch):
    """Verify that execution and assurance use the active candidate's SQL as the sole source of truth."""
    def fake_execute(req):
        return ExecutionResult(
            execution_id=f"fake_{req.execution_mode.value}",
            status=ExecutionStatus.SUCCESS,
            row_count=1,
            executed_sql=req.sql,
            execution_time_ms=10,
            dataset_id=req.dataset_id,
            dataset_hash="dummy_dataset_hash",
            query_hash="dummy_query_hash",
            result_path="",
            output_schema=None,
        )
    monkeypatch.setattr(ExecutionService, "execute", fake_execute)

    def fake_validate(*args, **kwargs):
        return ValidationReport(
            validation_id="fake_val",
            source_execution_id="fake_SOURCE",
            target_execution_id="fake_TARGET",
            overall_status="PASS",
            summary={"pass": 1, "fail": 0},
            checks=[]
        )
    monkeypatch.setattr(ValidationService, "validate_executions", fake_validate)

    def fake_score(*args, **kwargs):
        return AssuranceScore(evidence_score=100.0, evidence_coverage=100.0, components=[])
    monkeypatch.setattr(AssuranceScorer, "calculate", fake_score)

    orchestrator = MigrationOrchestrator()
    assurance_service = orchestrator._assurance_service

    # Create dummy migration record
    record = assurance_service.create_migration(
        source_dialect="NETEZZA",
        target_dialect="SNOWFLAKE",
        dataset_id="BOUNDARY_REFUND_001",
        source_sql="SELECT 1 as a",
        source_sql_hash="dummy_hash",
        dataset_hash="dummy_dataset_hash",
    )
    migration_id = record.migration_id

    from backend.translator.models import TranslationResult, TranslationStatus, TranslationResponse, TranslationMetadata

    mock_trans_res = TranslationResult(
        status=TranslationStatus.SUCCESS,
        candidate_validation_status="VALID_SYNTAX",
        response=TranslationResponse(target_sql="SELECT refund_amount", explanations=[]),
        metadata=TranslationMetadata(
            translation_id="test_trans_1",
            migration_id=migration_id,
            source_dialect="NETEZZA",
            target_dialect="SNOWFLAKE",
            source_sql_hash="dummy_hash",
            provider="dummy",
            model="dummy",
            request_id="dummy_req",
            translation_context_hash="dummy_ctx",
            prompt_hash="dummy_prompt",
            created_at="2024-01-01T00:00:00Z"
        )
    )

    # Add v1 candidate (simulating AI output)
    cand_v1 = create_candidate_version(
        migration_id=migration_id,
        sql_text="SELECT refund_amount",
        source="AI",
        parent_version_id=None
    )
    cand_v1.preflight_status = "BLOCKED"
    cand_v1.preflight_summary = PreflightSummary(
        status="BLOCKED",
        reason="Unknown column: refund_amount",
        execution_allowed=False,
        warnings=[]
    )
    save_candidate(cand_v1)

    # User edit: Add v2 candidate
    cand_v2 = create_candidate_version(
        migration_id=migration_id,
        sql_text="SELECT 1 as secondary_val",  # Valid SQL for duckdb execution
        source="USER",
        parent_version_id=cand_v1.candidate_id
    )
    cand_v2.preflight_status = "PASS"
    cand_v2.preflight_summary = PreflightSummary(
        status="PASS",
        reason="",
        execution_allowed=True,
        warnings=[]
    )
    save_candidate(cand_v2)

    # Run execute
    result = orchestrator.execute_migration(migration_id, translation_result=mock_trans_res, mock_mode="SUCCESS")
    
    # Assert Execution uses v2 SQL (Execution is returned indirectly via assurance report)
    report = result.assurance_report
    assert report is not None
    assert report.execution_summary is not None
    assert report.execution_summary.target_status == "SUCCESS"
    
    # Assert Assurance uses v2 SQL
    # evaluate_assurance passes the active candidate SQL to validation check
    # Check that it didn't throw an ImpossibleState exception!
    assert report.final_status.value != "FAILED"
    
    # Optional: ensure we can retrieve active candidate via API mockup
    active = get_active_candidate(migration_id)
    assert active.candidate_id == cand_v2.candidate_id
    assert active.sql_text == "SELECT 1 as secondary_val"

def test_user_corrected_candidate_resumes_pipeline(monkeypatch):
    """Verify that a corrected candidate successfully re-triggers the canonical runtime pipeline with correct candidate_id tracking."""
    def fake_execute(req):
        return ExecutionResult(
            execution_id=f"fake_{req.execution_mode.value}",
            status=ExecutionStatus.SUCCESS,
            row_count=1,
            executed_sql=req.sql,
            execution_time_ms=10,
            dataset_id=req.dataset_id,
            dataset_hash="dummy_dataset_hash",
            query_hash="dummy_query_hash",
            result_path="",
            output_schema=None,
        )
    monkeypatch.setattr(ExecutionService, "execute", fake_execute)

    def fake_validate(*args, **kwargs):
        return ValidationReport(
            validation_id="fake_val",
            source_execution_id="fake_SOURCE",
            target_execution_id="fake_TARGET",
            overall_status="PASS",
            summary={"pass": 1, "fail": 0},
            checks=[]
        )
    monkeypatch.setattr(ValidationService, "validate_executions", fake_validate)

    def fake_score(*args, **kwargs):
        return AssuranceScore(evidence_score=100.0, evidence_coverage=100.0, components=[])
    monkeypatch.setattr(AssuranceScorer, "calculate", fake_score)

    orchestrator = MigrationOrchestrator()
    assurance_service = orchestrator._assurance_service

    # Create dummy migration record
    record = assurance_service.create_migration(
        source_dialect="NETEZZA",
        target_dialect="SNOWFLAKE",
        dataset_id="BOUNDARY_REFUND_001",
        source_sql="SELECT 1 as a",
        source_sql_hash="dummy_hash",
        dataset_hash="dummy_dataset_hash",
    )
    migration_id = record.migration_id
    
    from backend.translator.models import TranslationResult, TranslationStatus, TranslationResponse, TranslationMetadata
    mock_trans_res = TranslationResult(
        status=TranslationStatus.SUCCESS,
        candidate_validation_status="VALID_SYNTAX",
        response=TranslationResponse(target_sql="SELECT refund_amount", explanations=[]),
        metadata=TranslationMetadata(
            translation_id="test_trans_1",
            migration_id=migration_id,
            source_dialect="NETEZZA",
            target_dialect="SNOWFLAKE",
            source_sql_hash="dummy_hash",
            provider="dummy",
            model="dummy",
            request_id="dummy_req",
            translation_context_hash="dummy_ctx",
            prompt_hash="dummy_prompt",
            created_at="2024-01-01T00:00:00Z"
        )
    )

    # v1 Candidate (AI - BLOCKED)
    cand_v1 = create_candidate_version(
        migration_id=migration_id,
        sql_text="SELECT refund_amount",
        source="AI",
        parent_version_id=None
    )
    cand_v1.preflight_status = "BLOCKED"
    cand_v1.preflight_summary = PreflightSummary(status="BLOCKED", reason="Unknown column", execution_allowed=False, warnings=[])
    save_candidate(cand_v1)
    
    # User edits candidate (v2 - PASS)
    cand_v2 = create_candidate_version(
        migration_id=migration_id,
        sql_text="SELECT secondary_val",
        source="USER",
        parent_version_id=cand_v1.candidate_id
    )
    cand_v2.preflight_status = "PASS"
    cand_v2.preflight_summary = PreflightSummary(status="PASS", reason="", execution_allowed=True, warnings=[])
    save_candidate(cand_v2)

    # User edit endpoint will call reset_downstream_pipeline_state
    assurance_service.reset_downstream_pipeline_state(migration_id, cand_v2.candidate_id)

    # Assert clean state before execution
    report = assurance_service.get_assurance_report(migration_id)
    if report:
        assert report.execution_summary is None
        assert report.validation_summary is None
        assert report.candidate_id == cand_v2.candidate_id
    
    mig = assurance_service.get_migration(migration_id)
    assert mig.final_status.value == "IN_PROGRESS"

    # Start the canonical pipeline execution
    result = orchestrator.execute_migration(migration_id, translation_result=mock_trans_res)
    final_report = result.assurance_report

    # Invariants tracking the active candidate through the pipeline
    assert final_report.candidate_id == cand_v2.candidate_id
    
    # We mock execution and validation, but we can verify it succeeded
    assert final_report.execution_summary is not None
    assert final_report.validation_summary is not None
    assert final_report.final_status.value == "VERIFIED"

def test_invalid_edit_after_successful_candidate_blocks_execution():
    """Verify that if a user submits a valid candidate, then submits an invalid one, the pipeline is blocked and no stale execution runs."""
    orchestrator = MigrationOrchestrator()
    assurance_service = orchestrator._assurance_service

    # Create dummy migration record
    record = assurance_service.create_migration(
        source_dialect="NETEZZA",
        target_dialect="SNOWFLAKE",
        dataset_id="TEST",
        source_sql="SELECT 1",
        source_sql_hash="dummy",
        dataset_hash="dummy",
    )
    migration_id = record.migration_id

    # v1 AI - BLOCKED
    cand_v1 = create_candidate_version(migration_id=migration_id, sql_text="SELECT 1", source="AI")
    cand_v1.preflight_status = "BLOCKED"
    cand_v1.preflight_summary = PreflightSummary(status="BLOCKED", reason="", execution_allowed=False, warnings=[])
    save_candidate(cand_v1)

    # v2 USER - PASS
    cand_v2 = create_candidate_version(migration_id=migration_id, sql_text="SELECT 2", source="USER", parent_version_id=cand_v1.candidate_id)
    cand_v2.preflight_status = "PASS"
    cand_v2.preflight_summary = PreflightSummary(status="PASS", reason="", execution_allowed=True, warnings=[])
    save_candidate(cand_v2)
    assurance_service.reset_downstream_pipeline_state(migration_id, cand_v2.candidate_id)

    # v3 USER - BLOCKED
    cand_v3 = create_candidate_version(migration_id=migration_id, sql_text="SELECT ERROR", source="USER", parent_version_id=cand_v2.candidate_id)
    cand_v3.preflight_status = "BLOCKED"
    cand_v3.preflight_summary = PreflightSummary(status="BLOCKED", reason="Error", execution_allowed=False, warnings=[])
    save_candidate(cand_v3)
    # The endpoint would update migration status directly
    from backend.assurance.models import MigrationFinalStatus
    record = assurance_service.get_migration(migration_id)
    record.final_status = MigrationFinalStatus.BLOCKED
    assurance_service._repository.save_migration(record)

    active = get_active_candidate(migration_id)
    assert active.candidate_id == cand_v3.candidate_id
    assert active.preflight_status == "BLOCKED"
    
    mig = assurance_service.get_migration(migration_id)
    assert mig.final_status.value == "BLOCKED"

    with pytest.raises(CandidateStateError) as exc_info:
        orchestrator.execute_migration(migration_id)
    assert "preflight is not PASS" in str(exc_info.value)

def test_candidate_execution_fails_safely_on_empty_sql(monkeypatch):
    """Verify that execution is blocked and no execution status is mutated when candidate SQL is missing."""
    def fake_execute(req):
        return ExecutionResult(
            execution_id=f"fake_{req.execution_mode.value}",
            status=ExecutionStatus.SUCCESS,
            row_count=1,
            executed_sql=req.sql,
            execution_time_ms=10,
            dataset_id=req.dataset_id,
            dataset_hash="dummy_dataset_hash",
            query_hash="dummy_query_hash",
            result_path="",
            output_schema=None,
        )
    monkeypatch.setattr(ExecutionService, "execute", fake_execute)

    orchestrator = MigrationOrchestrator()
    assurance_service = orchestrator._assurance_service

    # Create dummy migration record
    record = assurance_service.create_migration(
        source_dialect="NETEZZA",
        target_dialect="SNOWFLAKE",
        dataset_id="BOUNDARY_REFUND_001",
        source_sql="SELECT 1 as a",
        source_sql_hash="dummy_hash",
        dataset_hash="dummy_dataset_hash",
    )
    migration_id = record.migration_id

    # Create empty active candidate
    cand_empty = create_candidate_version(
        migration_id=migration_id,
        sql_text="",
        source="USER",
        parent_version_id=None
    )
    cand_empty.preflight_status = "PASS"
    cand_empty.preflight_summary = PreflightSummary(
        status="PASS",
        reason="",
        execution_allowed=True,
        warnings=[]
    )
    save_candidate(cand_empty)

    # Call API router directly to verify 409
    with pytest.raises(HTTPException) as exc_info:
        execute_migration(migration_id=migration_id)
        
    assert exc_info.value.status_code == 409
    assert "Active SQL candidate is missing or empty" in str(exc_info.value.detail)

    # Verify no execution was persisted
    report = assurance_service.get_assurance_report(migration_id)
    assert report is None or report.execution_summary is None or report.execution_summary.target_status != "SUCCESS"
