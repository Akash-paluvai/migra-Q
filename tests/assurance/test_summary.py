"""Tests for Phase 9 summary builders."""

import pytest

from backend.assurance.summary import SummaryBuilder
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


@pytest.fixture
def builder():
    return SummaryBuilder()


class TestTranslationSummary:
    def test_builds_from_result(self, builder):
        result = TranslationResult(
            metadata=TranslationMetadata(
                translation_id="TRN-001",
                request_id="REQ-001",
                provider="mock",
                model="mock-1",
                source_dialect="teradata",
                target_dialect="bigquery",
                source_sql_hash="abc",
                translation_context_hash="def",
                prompt_hash="ghi",
                created_at="2024-01-01",
            ),
            status=TranslationStatus.SUCCESS,
            candidate_validation_status=CandidateValidationStatus.VALID_SYNTAX,
            response=TranslationResponse(target_sql="SELECT 1"),
        )
        summary = builder.build_translation_summary(result)
        assert summary.translation_id == "TRN-001"
        assert summary.status == "SUCCESS"
        assert summary.candidate_validation_status == "VALID_SYNTAX"


class TestExecutionSummary:
    def test_builds_from_results(self, builder):
        src = ExecutionResult(
            execution_id="EXEC-SRC", query_hash="q1", dataset_id="dev",
            dataset_hash="dh1", status=ExecutionStatus.SUCCESS, row_count=100,
        )
        tgt = ExecutionResult(
            execution_id="EXEC-TGT", query_hash="q2", dataset_id="dev",
            dataset_hash="dh1", status=ExecutionStatus.SUCCESS, row_count=100,
        )
        summary = builder.build_execution_summary(src, tgt)
        assert summary.source_execution_id == "EXEC-SRC"
        assert summary.target_execution_id == "EXEC-TGT"
        assert summary.source_row_count == 100


class TestValidationSummary:
    def test_builds_checks(self, builder):
        report = ValidationReport(
            validation_id="VAL-001",
            source_execution_id="EXEC-SRC",
            target_execution_id="EXEC-TGT",
            checks=[
                ValidationResult(
                    check_name="SchemaValidator", status=ValidationCheckStatus.PASS,
                    score=1.0, severity=ValidationSeverity.HIGH, summary="ok",
                ),
            ],
        )
        summary = builder.build_validation_summary(report)
        assert summary.validation_id == "VAL-001"
        assert len(summary.checks) == 1
        assert summary.checks[0].check_name == "SchemaValidator"


class TestDiscrepancySummary:
    def test_none_input(self, builder):
        summary = builder.build_discrepancy_summary(None)
        assert summary.discrepancy_count == 0

    def test_with_discrepancies(self, builder):
        report = DiscrepancyReport(
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
                    classification_reason="Boundary",
                    affected_row_count=6142,
                    created_at="2024-01-01",
                ),
            ],
            discrepancy_count=1,
            category_counts={"BOUNDARY_CONDITION": 1},
            severity_counts={"HIGH": 1},
        )
        summary = builder.build_discrepancy_summary(report)
        assert summary.discrepancy_count == 1
        assert summary.total_affected_rows == 6142


class TestDiagnosisSummary:
    def test_none_input(self, builder):
        summary = builder.build_diagnosis_summary(None)
        assert summary.diagnosis_id == ""

    def test_with_result(self, builder):
        result = DiagnosisAIResult(
            metadata=DiagnosisAIMetadata(
                diagnosis_id="AIDIAG-001",
                discrepancy_id="D-001",
                provider="mock",
                model="mock-1",
                context_hash="abc",
                prompt_hash="def",
            ),
            diagnosis=AIDiagnosis(
                diagnosis_id="AIDIAG-001",
                discrepancy_id="D-001",
                observed_change="Changed > to >=",
                diagnosis_confidence=0.95,
            ),
            repair_proposal=RepairProposal(
                repair_id="REP-001",
                discrepancy_id="D-001",
                status=RepairStatus.PROPOSED,
                original_sql="SELECT 1",
                proposed_sql="SELECT 2",
            ),
        )
        summary = builder.build_diagnosis_summary(result)
        assert summary.diagnosis_id == "AIDIAG-001"
        assert summary.observed_change == "Changed > to >="


class TestVerificationSummary:
    def test_none_input(self, builder):
        summary = builder.build_verification_summary(None)
        assert summary.verification_id is None

    def test_with_result(self, builder):
        result = RepairVerificationResult(
            verification_id="VER-001",
            repair_id="REP-001",
            discrepancy_id="D-001",
            validation_id_before="VAL-001",
            validation_id_after="VAL-002",
            execution_id_before="EXEC-001",
            execution_id_repaired="EXEC-002",
            status=VerificationStatus.VERIFIED,
            original_discrepancy_count=1,
            remaining_discrepancy_count=0,
            new_discrepancy_count=0,
            resolved_discrepancy_count=1,
            affected_rows_before=6142,
            affected_rows_after=0,
            reduction_percentage=100.0,
            metadata=VerificationMetadata(
                verification_id="VER-001", repair_id="REP-001",
                discrepancy_id="D-001", validation_id_before="VAL-001",
                execution_id_before="EXEC-001", dataset_id="dev",
                dataset_hash_before="abc", dataset_hash_after="abc",
                validation_config_hash_before="cfg1", validation_config_hash_after="cfg1",
            ),
        )
        summary = builder.build_verification_summary(result)
        assert summary.verification_id == "VER-001"
        assert summary.remaining_discrepancy_count == 0
        assert summary.reduction_percentage == 100.0
