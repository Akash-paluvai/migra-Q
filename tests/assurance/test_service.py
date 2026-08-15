"""Tests for Phase 9 MigrationAssuranceService — end-to-end integration."""


from backend.assurance.models import MigrationFinalStatus, VerificationPath
from backend.assurance.service import MigrationAssuranceService
from backend.diagnosis.models import (
    ClassificationMethod,
    DiscrepancyCategory,
    DiscrepancyRecord,
    DiscrepancyReport,
    DiscrepancySeverity,
)
from backend.diagnosis_ai.models import (
    AIDiagnosis,
    DiagnosisAIMetadata,
    DiagnosisAIResult,
    RepairProposal,
    RepairStatus,
)
from backend.execution.models import ExecutionResult, ExecutionStatus
from backend.repair_verification.models import (
    RepairVerificationResult,
    VerificationMetadata,
    VerificationStatus,
)
from backend.translator.models import (
    CandidateValidationStatus,
    TranslationMetadata,
    TranslationResponse,
    TranslationResult,
    TranslationStatus,
)
from backend.validation.models import (
    ValidationCheckStatus,
    ValidationReport,
    ValidationResult,
    ValidationSeverity,
)


def _make_translation():
    return TranslationResult(
        metadata=TranslationMetadata(
            translation_id="TRN-001", request_id="REQ-001",
            provider="mock", model="mock-1",
            source_dialect="teradata", target_dialect="bigquery",
            source_sql_hash="abc", translation_context_hash="def",
            prompt_hash="ghi", created_at="2024-01-01",
        ),
        status=TranslationStatus.SUCCESS,
        candidate_validation_status=CandidateValidationStatus.VALID_SYNTAX,
        response=TranslationResponse(target_sql="SELECT 1"),
    )


def _make_executions():
    src = ExecutionResult(
        execution_id="EXEC-SRC", query_hash="q1", dataset_id="dev",
        dataset_hash="dh1", status=ExecutionStatus.SUCCESS, row_count=175467,
    )
    tgt = ExecutionResult(
        execution_id="EXEC-TGT", query_hash="q2", dataset_id="dev",
        dataset_hash="dh1", status=ExecutionStatus.SUCCESS, row_count=175467,
    )
    return src, tgt


def _make_validation_pass():
    return ValidationReport(
        validation_id="VAL-001",
        source_execution_id="EXEC-SRC",
        target_execution_id="EXEC-TGT",
        overall_status="PASS",
        checks=[
            ValidationResult(check_name="SchemaValidator", status=ValidationCheckStatus.PASS, score=1.0, severity=ValidationSeverity.HIGH, summary="ok"),
            ValidationResult(check_name="RowValidator", status=ValidationCheckStatus.PASS, score=1.0, severity=ValidationSeverity.HIGH, summary="ok"),
            ValidationResult(check_name="AggregateValidator", status=ValidationCheckStatus.PASS, score=1.0, severity=ValidationSeverity.HIGH, summary="ok"),
            ValidationResult(check_name="BusinessRuleValidator", status=ValidationCheckStatus.SKIPPED, score=0.0, severity=ValidationSeverity.HIGH, summary="skipped"),
            ValidationResult(check_name="EdgeCaseValidator", status=ValidationCheckStatus.PASS, score=1.0, severity=ValidationSeverity.HIGH, summary="ok"),
        ],
    )


def _make_validation_fail():
    return ValidationReport(
        validation_id="VAL-001",
        source_execution_id="EXEC-SRC",
        target_execution_id="EXEC-TGT",
        overall_status="FAIL",
        checks=[
            ValidationResult(check_name="SchemaValidator", status=ValidationCheckStatus.PASS, score=1.0, severity=ValidationSeverity.HIGH, summary="ok"),
            ValidationResult(check_name="RowValidator", status=ValidationCheckStatus.FAIL, score=0.96, severity=ValidationSeverity.HIGH, summary="mismatches", mismatch_count=1),
            ValidationResult(check_name="AggregateValidator", status=ValidationCheckStatus.PASS, score=1.0, severity=ValidationSeverity.HIGH, summary="ok"),
            ValidationResult(check_name="BusinessRuleValidator", status=ValidationCheckStatus.SKIPPED, score=0.0, severity=ValidationSeverity.HIGH, summary="skipped"),
            ValidationResult(check_name="EdgeCaseValidator", status=ValidationCheckStatus.PASS, score=1.0, severity=ValidationSeverity.HIGH, summary="ok"),
        ],
    )


def _make_discrepancy_report():
    return DiscrepancyReport(
        diagnosis_id="DIAG-001",
        validation_id="VAL-001",
        discrepancies=[
            DiscrepancyRecord(
                discrepancy_id="D-001",
                validation_id="VAL-001",
                category=DiscrepancyCategory.BOUNDARY_CONDITION,
                severity=DiscrepancySeverity.HIGH,
                classification_confidence=1.0,
                classification_method=ClassificationMethod.DETERMINISTIC_RULE,
                classification_reason="Boundary condition",
                affected_row_count=6142,
                created_at="2024-01-01",
            ),
        ],
        discrepancy_count=1,
        category_counts={"BOUNDARY_CONDITION": 1},
        severity_counts={"HIGH": 1},
    )


def _make_diagnosis_ai():
    return DiagnosisAIResult(
        metadata=DiagnosisAIMetadata(
            diagnosis_id="AIDIAG-001", discrepancy_id="D-001",
            provider="mock", model="mock-1",
            context_hash="abc", prompt_hash="def",
        ),
        diagnosis=AIDiagnosis(
            diagnosis_id="AIDIAG-001", discrepancy_id="D-001",
            observed_change="Changed > to >=",
        ),
        repair_proposal=RepairProposal(
            repair_id="REP-001", discrepancy_id="D-001",
            status=RepairStatus.PROPOSED,
            original_sql="SELECT 1", proposed_sql="SELECT 2",
        ),
    )


def _make_verification():
    return RepairVerificationResult(
        verification_id="VER-001", repair_id="REP-001", discrepancy_id="D-001",
        validation_id_before="VAL-001", validation_id_after="VAL-002",
        execution_id_before="EXEC-TGT", execution_id_repaired="EXEC-REP",
        status=VerificationStatus.VERIFIED,
        original_discrepancy_count=1, remaining_discrepancy_count=0,
        new_discrepancy_count=0, resolved_discrepancy_count=1,
        affected_rows_before=6142, affected_rows_after=0,
        reduction_percentage=100.0,
        metadata=VerificationMetadata(
            verification_id="VER-001", repair_id="REP-001",
            discrepancy_id="D-001", validation_id_before="VAL-001",
            execution_id_before="EXEC-TGT", dataset_id="dev",
            dataset_hash_before="dh1", dataset_hash_after="dh1",
            validation_config_hash_before="cfg1", validation_config_hash_after="cfg1",
        ),
    )


class TestServiceDirectPass:
    def test_verified_no_discrepancies(self):
        service = MigrationAssuranceService()
        migration = service.create_migration(
            source_dialect="teradata", target_dialect="bigquery",
            source_sql_hash="abc", dataset_id="dev", dataset_hash="dh1",
        )
        report = service.evaluate_assurance(
            migration_id=migration.migration_id,
            translation_result=_make_translation(),
            source_execution=_make_executions()[0],
            target_execution=_make_executions()[1],
            validation_report=_make_validation_pass(),
        )
        assert report.final_status == MigrationFinalStatus.VERIFIED
        assert report.verification_path == VerificationPath.DIRECT_PASS
        assert report.score.evidence_score == 100.0
        assert report.score.evidence_coverage == 75.0
        assert report.gate_evaluation.all_passed is True


class TestServiceRepairedPass:
    def test_verified_after_repair(self):
        service = MigrationAssuranceService()
        migration = service.create_migration(
            source_dialect="teradata", target_dialect="bigquery",
            source_sql_hash="abc", dataset_id="dev", dataset_hash="dh1",
        )
        report = service.evaluate_assurance(
            migration_id=migration.migration_id,
            translation_result=_make_translation(),
            source_execution=_make_executions()[0],
            target_execution=_make_executions()[1],
            validation_report=_make_validation_fail(),
            discrepancy_report=_make_discrepancy_report(),
            diagnosis_ai_result=_make_diagnosis_ai(),
            repair_verification_result=_make_verification(),
        )
        assert report.final_status == MigrationFinalStatus.VERIFIED
        assert report.verification_path == VerificationPath.REPAIRED_PASS
        assert report.gate_evaluation.all_passed is True
        assert report.lineage.is_complete is True


class TestServiceBlocked:
    def test_blocked_unresolved_discrepancy(self):
        service = MigrationAssuranceService()
        migration = service.create_migration(
            source_dialect="teradata", target_dialect="bigquery",
            source_sql_hash="abc", dataset_id="dev", dataset_hash="dh1",
        )
        # Discrepancies found but no repair attempted
        report = service.evaluate_assurance(
            migration_id=migration.migration_id,
            translation_result=_make_translation(),
            source_execution=_make_executions()[0],
            target_execution=_make_executions()[1],
            validation_report=_make_validation_fail(),
            discrepancy_report=_make_discrepancy_report(),
        )
        assert report.final_status == MigrationFinalStatus.BLOCKED
        assert report.gate_evaluation.all_passed is False


class TestServicePersistence:
    def test_report_persisted(self):
        service = MigrationAssuranceService()
        migration = service.create_migration(
            source_dialect="teradata", target_dialect="bigquery",
            source_sql_hash="abc", dataset_id="dev", dataset_hash="dh1",
        )
        service.evaluate_assurance(
            migration_id=migration.migration_id,
            translation_result=_make_translation(),
            source_execution=_make_executions()[0],
            target_execution=_make_executions()[1],
            validation_report=_make_validation_pass(),
        )
        retrieved = service.get_assurance_report(migration.migration_id)
        assert retrieved is not None
        assert retrieved.migration_id == migration.migration_id

    def test_migration_updated_after_evaluation(self):
        service = MigrationAssuranceService()
        migration = service.create_migration(
            source_dialect="teradata", target_dialect="bigquery",
            source_sql_hash="abc", dataset_id="dev", dataset_hash="dh1",
        )
        service.evaluate_assurance(
            migration_id=migration.migration_id,
            translation_result=_make_translation(),
            source_execution=_make_executions()[0],
            target_execution=_make_executions()[1],
            validation_report=_make_validation_pass(),
        )
        updated = service.get_migration(migration.migration_id)
        assert updated is not None
        assert updated.final_status == MigrationFinalStatus.VERIFIED
        assert updated.assurance_score == 100.0


class TestServiceLimitations:
    def test_skipped_validator_limitation(self):
        service = MigrationAssuranceService()
        migration = service.create_migration(
            source_dialect="teradata", target_dialect="bigquery",
            source_sql_hash="abc", dataset_id="dev", dataset_hash="dh1",
        )
        report = service.evaluate_assurance(
            migration_id=migration.migration_id,
            translation_result=_make_translation(),
            source_execution=_make_executions()[0],
            target_execution=_make_executions()[1],
            validation_report=_make_validation_pass(),
        )
        assert any("coverage" in lim.lower() or "skipped" in lim.lower() for lim in report.limitations)
