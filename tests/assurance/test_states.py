import pytest
from backend.assurance.models import VerificationPath, MigrationFinalStatus, MigrationState
from backend.assurance.service import MigrationAssuranceService
from backend.validation.models import ValidationReport, ValidationResult, ValidationCheckStatus
from backend.diagnosis.models import DiscrepancyReport, DiscrepancyRecord
from backend.diagnosis_ai.models import DiagnosisAIResult, AIDiagnosis, RepairProposal, DiagnosisStatus, RepairStatus, DiagnosisAIMetadata
from backend.repair_verification.models import RepairVerificationResult, VerificationStatus, VerificationMetadata
from backend.execution.models import ExecutionResult, ExecutionStatus
from backend.translator.models import TranslationResult, TranslationStatus, CandidateValidationStatus, TranslationMetadata, TranslationResponse
from datetime import datetime, timezone

def _create_base_mocks():
    translation = TranslationResult(
        status=TranslationStatus.SUCCESS,
        candidate_validation_status=CandidateValidationStatus.VALID_SYNTAX,
        metadata=TranslationMetadata.model_construct(translation_id="t1", source_dialect="s", target_dialect="t", provider="p", model="m", created_at=""),
        response=TranslationResponse.model_construct(target_sql="sql")
    )
    src_exec = ExecutionResult.model_construct(execution_id="e1", status=ExecutionStatus.SUCCESS, row_count=10, dataset_id="d1", dataset_hash="h1")
    tgt_exec = ExecutionResult.model_construct(execution_id="e2", status=ExecutionStatus.SUCCESS, row_count=10, dataset_id="d1", dataset_hash="h1")
    return translation, src_exec, tgt_exec

def test_direct_pass_state():
    service = MigrationAssuranceService()
    translation, src, tgt = _create_base_mocks()
    
    val = ValidationReport(
        validation_id="v1", source_execution_id="e1", target_execution_id="e2",
        dataset_id="d1", overall_status="PASS", checks=[ValidationResult.model_construct(check_name="c1", status=ValidationCheckStatus.PASS, score=1.0, severity="INFO", summary="", mismatch_count=0)]
    )
    
    report = service.evaluate_assurance(
        migration_id="m1", translation_result=translation, source_execution=src,
        target_execution=tgt, validation_report=val, discrepancy_report=None,
        diagnosis_ai_result=None, repair_verification_result=None
    )
    
    assert report.validation_summary.overall_status == "PASS"
    assert report.repair_summary.status == "NOT_EXECUTED" or report.repair_summary.repair_id == ""
    assert report.verification_summary.status == "NOT_EXECUTED"
    assert report.lineage.verification_path == VerificationPath.DIRECT_PASS
    assert report.final_status == MigrationFinalStatus.VERIFIED
    assert report.lineage.is_complete is True

def test_repaired_pass_state():
    service = MigrationAssuranceService()
    translation, src, tgt = _create_base_mocks()
    
    val = ValidationReport(
        validation_id="v1", source_execution_id="e1", target_execution_id="e2",
        dataset_id="d1", overall_status="FAIL", checks=[ValidationResult.model_construct(check_name="c1", status=ValidationCheckStatus.FAIL, score=0, severity="HIGH", summary="", mismatch_count=1)]
    )
    disc = DiscrepancyReport.model_construct(diagnosis_id="d1", validation_id="v1", discrepancy_count=1, category_counts={}, severity_counts={"HIGH": 1}, discrepancies=[])
    
    ai_res = DiagnosisAIResult(
        metadata=DiagnosisAIMetadata.model_construct(diagnosis_id="ai1", discrepancy_id="d_id", created_at=""),
        diagnosis=AIDiagnosis.model_construct(diagnosis_id="ai1", discrepancy_id="d_id", status=DiagnosisStatus.DIAGNOSED, observed_change="", likely_mechanism="", possible_cause="", uncertainty="", diagnosis_confidence=1.0),
        repair_proposal=RepairProposal.model_construct(repair_id="r1", discrepancy_id="d_id", status=RepairStatus.PROPOSED, original_sql="", proposed_sql="", repair_confidence=1.0, changed_region="")
    )
    
    ver = RepairVerificationResult(
        verification_id="ver1", repair_id="r1", discrepancy_id="d_id", status=VerificationStatus.VERIFIED,
        original_discrepancy_count=1, remaining_discrepancy_count=0, new_discrepancy_count=0, resolved_discrepancy_count=1,
        affected_rows_before=1, affected_rows_after=1, reduction_percentage=100.0,
        original_target_sql="", repaired_target_sql="", summary="", metadata=VerificationMetadata.model_construct(dataset_hash_before="", dataset_hash_after="", validation_config_hash_before="", validation_config_hash_after=""),
        validation_id_before="v1", execution_id_before="e2"
    )
    
    report = service.evaluate_assurance(
        migration_id="m1", translation_result=translation, source_execution=src,
        target_execution=tgt, validation_report=val, discrepancy_report=disc,
        diagnosis_ai_result=ai_res, repair_verification_result=ver
    )
    
    assert report.validation_summary.overall_status == "FAIL"
    assert report.repair_summary.status == "PROPOSED"
    assert report.verification_summary.status == "VERIFIED"
    assert report.lineage.verification_path == VerificationPath.REPAIRED_PASS
    assert report.final_status == MigrationFinalStatus.VERIFIED
    assert report.lineage.is_complete is True

def test_repair_failed_state():
    service = MigrationAssuranceService()
    translation, src, tgt = _create_base_mocks()
    
    val = ValidationReport(
        validation_id="v1", source_execution_id="e1", target_execution_id="e2",
        dataset_id="d1", overall_status="FAIL", checks=[ValidationResult.model_construct(check_name="c1", status=ValidationCheckStatus.FAIL, score=0, severity="HIGH", summary="", mismatch_count=1)]
    )
    disc = DiscrepancyReport.model_construct(diagnosis_id="d1", validation_id="v1", discrepancy_count=1, category_counts={}, severity_counts={"HIGH": 1}, discrepancies=[])
    
    ai_res = DiagnosisAIResult(
        metadata=DiagnosisAIMetadata.model_construct(diagnosis_id="ai1", discrepancy_id="d_id", created_at=""),
        diagnosis=AIDiagnosis.model_construct(diagnosis_id="ai1", discrepancy_id="d_id", status=DiagnosisStatus.DIAGNOSED, observed_change="", likely_mechanism="", possible_cause="", uncertainty="", diagnosis_confidence=1.0),
        repair_proposal=RepairProposal.model_construct(repair_id="r1", discrepancy_id="d_id", status=RepairStatus.FAILED, original_sql="", proposed_sql="", repair_confidence=1.0, changed_region="")
    )
    
    report = service.evaluate_assurance(
        migration_id="m1", translation_result=translation, source_execution=src,
        target_execution=tgt, validation_report=val, discrepancy_report=disc,
        diagnosis_ai_result=ai_res, repair_verification_result=None
    )
    
    assert report.validation_summary.overall_status == "FAIL"
    assert report.repair_summary.status == "FAILED"
    assert report.verification_summary.status == "NOT_EXECUTED"
    assert report.verification_summary.verification_id is None
    assert report.lineage.verification_path == VerificationPath.REPAIR_FAILED
    assert report.lineage.is_complete is False
    assert report.final_status == MigrationFinalStatus.BLOCKED
    assert report.lineage.verification_path != VerificationPath.DIRECT_PASS
    assert report.lineage.verification_path != VerificationPath.REPAIRED_PASS

def test_failed_validation_cannot_produce_direct_pass():
    service = MigrationAssuranceService()
    translation, src, tgt = _create_base_mocks()
    
    val = ValidationReport(
        validation_id="v1", source_execution_id="e1", target_execution_id="e2",
        dataset_id="d1", overall_status="FAIL", checks=[ValidationResult.model_construct(check_name="c1", status=ValidationCheckStatus.FAIL, score=0, severity="HIGH", summary="", mismatch_count=1)]
    )
    
    # Missing AI diagnosis and repair results
    report = service.evaluate_assurance(
        migration_id="m1", translation_result=translation, source_execution=src,
        target_execution=tgt, validation_report=val, discrepancy_report=None,
        diagnosis_ai_result=None, repair_verification_result=None
    )
    
    assert report.final_status == MigrationFinalStatus.BLOCKED
    assert report.lineage.verification_path != VerificationPath.DIRECT_PASS
    assert report.lineage.is_complete is False
    assert report.lineage.verification_path == VerificationPath.REPAIR_NOT_EXECUTED

def test_provider_limit_state():
    service = MigrationAssuranceService()
    translation = TranslationResult(
        status=TranslationStatus.FAILED,
        candidate_validation_status=CandidateValidationStatus.NOT_EVALUATED,
        metadata=TranslationMetadata.model_construct(translation_id="t1", source_dialect="s", target_dialect="t", provider="p", model="m", created_at="", error_code="PROVIDER_TOKEN_EXHAUSTED", error_message="limit"),
        response=None
    )
    
    report = service.evaluate_assurance(
        migration_id="m1", translation_result=translation, source_execution=None,
        target_execution=None, validation_report=None, discrepancy_report=None,
        diagnosis_ai_result=None, repair_verification_result=None
    )
    
    assert report.final_status == MigrationFinalStatus.BLOCKED_PROVIDER_LIMIT
