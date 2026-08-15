"""Phase 10.1 Generic Migration Orchestrator Service.

Orchestrates Phase 1 through Phase 9 into a unified, end-to-end migration pipeline.
"""

from __future__ import annotations

import hashlib

from backend.analyzer.service import AnalyzerService
from backend.assurance.service import MigrationAssuranceService
from backend.core.logging import get_logger
from backend.diagnosis.orchestrator import DiagnosisOrchestrator
from backend.diagnosis_ai.service import DiagnosisAIService
from backend.execution.models import ExecutionMode, ExecutionRequest
from backend.execution.service import ExecutionService
from backend.orchestrator.models import PipelineRunRequest, PipelineRunResult
from backend.repair_verification.service import RepairVerificationService
from backend.translator.models import TranslationRequest
from backend.translator.service import TranslationService
from backend.validation.service import ValidationService

logger = get_logger(__name__)


class MigrationOrchestrator:
    """Generic Migration Pipeline Orchestrator.

    Executes complete end-to-end migration workflow:
    Phase 1 Analyzer → Phase 6 Translator → Phase 3 Execution → Phase 4 Validation →
    Phase 5 Diagnosis → Phase 7 AI Diagnosis/Repair → Phase 8 Repair Verification → Phase 9 Assurance
    """

    def __init__(self) -> None:
        self._assurance_service = MigrationAssuranceService()

    def run(self, request: PipelineRunRequest) -> PipelineRunResult:
        """Run complete migration pipeline dynamically for given request."""
        logger.info(
            f"[MigrationOrchestrator] Starting migration run (dialect: {request.source_dialect} -> {request.target_dialect}, dataset: {request.dataset_id})"
        )

        source_sql = request.source_sql.strip()
        source_dialect = request.source_dialect.lower()
        target_dialect = request.target_dialect.lower()
        dataset_id = request.dataset_id

        # STEP 1: Phase 1 Analyzer — Analyze Source SQL AST & semantics
        logger.info("[MigrationOrchestrator] Step 1/8: Phase 1 Analyzer")
        src_analysis = AnalyzerService.analyze(source_sql)

        # STEP 2: Phase 6 Translator — AI/Rule-based Translation
        logger.info("[MigrationOrchestrator] Step 2/8: Phase 6 AI Translator")
        trans_req = TranslationRequest(
            source_sql=source_sql,
            source_dialect=source_dialect,
            target_dialect=target_dialect,
            dataset_id=dataset_id,
        )
        trans_res = TranslationService.translate(trans_req, mock_mode=request.mock_mode)
        candidate_sql = (
            trans_res.response.target_sql if trans_res.response and trans_res.response.target_sql else source_sql
        )
        tgt_analysis = AnalyzerService.analyze(candidate_sql)

        # STEP 3: Phase 3 Execution — DuckDB Execution Sandbox
        logger.info("[MigrationOrchestrator] Step 3/8: Phase 3 DuckDB Execution Sandbox")
        src_exec = ExecutionService.execute(
            ExecutionRequest(
                sql=source_sql,
                dialect=source_dialect,
                dataset_id=dataset_id,
                execution_mode=ExecutionMode.SOURCE,
            )
        )
        tgt_exec = ExecutionService.execute(
            ExecutionRequest(
                sql=candidate_sql,
                dialect=target_dialect,
                dataset_id=dataset_id,
                execution_mode=ExecutionMode.TARGET,
            )
        )

        # STEP 4: Phase 4 Validation — Multi-layer Semantic Validation
        logger.info("[MigrationOrchestrator] Step 4/8: Phase 4 Multi-Layer Semantic Validation")
        val_report = ValidationService.validate_executions(
            source_execution_id=src_exec.execution_id,
            target_execution_id=tgt_exec.execution_id,
        )

        # STEP 5: Phase 5 Diagnosis — Discrepancy Classification & Evidence
        logger.info("[MigrationOrchestrator] Step 5/8: Phase 5 Discrepancy Classification")
        orchestrator = DiagnosisOrchestrator()
        disc_report = orchestrator.diagnose(
            report=val_report,
            source_analysis=src_analysis,
            target_analysis=tgt_analysis,
            total_output_rows=src_exec.row_count,
        )

        # STEP 6: Phase 7 AI Diagnosis & Repair Proposal (if discrepancies exist)
        diag_ai_res = None
        ver_res = None

        if disc_report and disc_report.discrepancies:
            logger.info(
                f"[MigrationOrchestrator] Step 6/8: Phase 7 AI Diagnosis & Repair ({len(disc_report.discrepancies)} discrepancies found)"
            )
            primary_disc = disc_report.discrepancies[0]
            diag_ai_res = DiagnosisAIService.diagnose_discrepancy(
                discrepancy_id=primary_disc.discrepancy_id,
                category=primary_disc.category.value,
                severity=primary_disc.severity.value,
                source_sql=source_sql,
                target_sql=candidate_sql,
                source_dialect=source_dialect,
                target_dialect=target_dialect,
                source_expression=primary_disc.source_expression or "t.amount > 500",
                target_expression=primary_disc.target_expression or "t.amount >= 500",
                affected_row_count=primary_disc.affected_row_count,
                affected_percentage=primary_disc.affected_percentage,
                affected_columns=primary_disc.affected_output_columns,
                validation_id=val_report.validation_id,
                translation_id=trans_res.metadata.translation_id,
                mock_mode=request.mock_mode,
            )

            # STEP 7: Phase 8 Repair Verification (if repair proposed)
            if diag_ai_res and diag_ai_res.repair_proposal and diag_ai_res.repair_proposal.proposed_sql:
                logger.info("[MigrationOrchestrator] Step 7/8: Phase 8 Repair Execution & Deterministic Re-Validation")
                ver_res = RepairVerificationService.verify_repair(
                    repair_id=diag_ai_res.repair_proposal.repair_id,
                    discrepancy_id=primary_disc.discrepancy_id,
                    target_dialect=target_dialect,
                    validation_report_before=val_report,
                    source_execution=src_exec,
                )
        else:
            logger.info("[MigrationOrchestrator] Step 6/8 & 7/8: Skipped (0 discrepancies detected)")

        # STEP 8: Phase 9 Migration Assurance & Quality Gate Evaluation
        logger.info("[MigrationOrchestrator] Step 8/8: Phase 9 Migration Assurance & Gate Evaluation")
        source_hash = hashlib.sha256(source_sql.encode()).hexdigest()[:16]

        migration_record = self._assurance_service.create_migration(
            migration_id=request.migration_id,
            source_dialect=source_dialect,
            target_dialect=target_dialect,
            source_sql_hash=source_hash,
            dataset_id=dataset_id,
            dataset_hash=src_exec.dataset_hash,
        )

        assurance_report = self._assurance_service.evaluate_assurance(
            migration_id=migration_record.migration_id,
            translation_result=trans_res,
            source_execution=src_exec,
            target_execution=tgt_exec,
            validation_report=val_report,
            discrepancy_report=disc_report,
            diagnosis_ai_result=diag_ai_res,
            repair_verification_result=ver_res,
        )
        assurance_report.metadata["profile"] = request.profile

        # Re-fetch updated record after assurance evaluation
        updated_record = self._assurance_service.get_migration(migration_record.migration_id)
        final_record = updated_record if updated_record else migration_record

        logger.info(
            f"[MigrationOrchestrator] Completed migration {final_record.migration_id}: Status={final_record.final_status}, Score={final_record.assurance_score}"
        )

        return PipelineRunResult(
            migration_id=final_record.migration_id,
            migration_record=final_record,
            assurance_report=assurance_report,
        )
