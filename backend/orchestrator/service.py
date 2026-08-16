"""Phase 10.1 Generic Migration Orchestrator Service.

Orchestrates Phase 1 through Phase 9 into a unified, end-to-end migration pipeline.
"""

from __future__ import annotations

import hashlib
from typing import Any

from backend.analyzer.service import AnalyzerService
from backend.assurance.service import MigrationAssuranceService
from backend.core.logging import get_logger
from backend.diagnosis.orchestrator import DiagnosisOrchestrator
from backend.diagnosis_ai.service import DiagnosisAIService
from backend.execution.models import ExecutionMode, ExecutionRequest, ExecutionStatus
from backend.execution.service import ExecutionService
from backend.orchestrator.models import PipelineRunRequest, PipelineRunResult
from backend.repair_verification.service import RepairVerificationService
from backend.translator.models import TranslationRequest, TranslationStatus
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

    def preflight_check(self, source_sql: str, dataset_id: str) -> dict[str, Any]:
        """Perform preflight validation check for SQL & dataset compatibility."""
        from backend.datasets.registry import DatasetRegistry

        registry = DatasetRegistry()
        if not registry.exists(dataset_id):
            raise ValueError(f"DATASET_NOT_FOUND: Dataset '{dataset_id}' is not registered.")

        # Parse SQL syntax with AnalyzerService
        src_analysis = AnalyzerService.analyze(source_sql)

        # Check referenced tables against dataset table schemas
        table_summaries = registry.resolve_schema(dataset_id)
        available_tables = {t.table_name.lower() for t in table_summaries}

        referenced_tables = [
            (t.name if hasattr(t, "name") else str(t)).lower()
            for t in src_analysis.tables
        ]
        missing_tables = [t for t in referenced_tables if t not in available_tables]

        if missing_tables:
            raise ValueError(
                f"DATASET_SCHEMA_MISMATCH: Referenced table(s) {missing_tables} not found in dataset '{dataset_id}'. Available tables: {list(available_tables)}"
            )

        return {
            "sql_parsed": True,
            "referenced_tables": referenced_tables,
            "available_tables": list(available_tables),
            "status": "COMPATIBLE",
        }

    def run(self, request: PipelineRunRequest) -> PipelineRunResult:
        """Run complete migration pipeline dynamically for given request."""
        source_sql = request.source_sql.strip()
        source_dialect = request.source_dialect.lower()
        target_dialect = request.target_dialect.lower()
        dataset_id = request.dataset_id

        # STEP 0: Preflight Compatibility & Schema Check
        self.preflight_check(source_sql, dataset_id)

        # STEP 0.5: Generate root identity & create MigrationRecord(CREATED) early
        import uuid
        migration_id = request.migration_id or f"MIG-{uuid.uuid4().hex[:12].upper()}"
        source_hash = hashlib.sha256(source_sql.encode()).hexdigest()[:16]

        logger.info(
            f"[MigrationOrchestrator] [{migration_id}] Starting run (source_hash: {source_hash}, dialect: {source_dialect} -> {target_dialect}, dataset: {dataset_id})"
        )

        migration_record = self._assurance_service.create_migration(
            migration_id=migration_id,
            source_dialect=source_dialect,
            target_dialect=target_dialect,
            source_sql_hash=source_hash,
            dataset_id=dataset_id,
            dataset_hash="pending",
        )

        # STEP 1: Phase 1 Analyzer — Analyze Source SQL AST & semantics
        logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 1/8: Phase 1 Analyzer")
        src_analysis = AnalyzerService.analyze(source_sql)

        # STEP 2: Phase 6 Translator — AI/Rule-based Translation
        logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 2/8: Phase 6 AI Translator")
        trans_req = TranslationRequest(
            source_sql=source_sql,
            source_dialect=source_dialect,
            target_dialect=target_dialect,
            dataset_id=dataset_id,
            migration_id=migration_id,
        )
        trans_res = TranslationService.translate(trans_req, mock_mode=request.mock_mode)
        if hasattr(trans_res, "metadata") and trans_res.metadata:
            trans_res.metadata.migration_id = migration_id
            trans_res.metadata.source_sql_hash = source_hash

        # STRICT LIFECYCLE CHECK: If translation failed, do NOT proceed downstream
        if trans_res.status != TranslationStatus.SUCCESS or not trans_res.response or not trans_res.response.target_sql:
            logger.warning(
                f"[MigrationOrchestrator] [{migration_id}] Translation failed with status={trans_res.status}. "
                f"Halting pipeline execution. Downstream phases will NOT be run."
            )
            assurance_report = self._assurance_service.evaluate_assurance(
                migration_id=migration_id,
                translation_result=trans_res,
                source_execution=None,
                target_execution=None,
                validation_report=None,
                discrepancy_report=None,
                diagnosis_ai_result=None,
                repair_verification_result=None,
            )
            assurance_report.metadata["profile"] = request.profile
            updated_record = self._assurance_service.get_migration(migration_id)
            final_record = updated_record if updated_record else migration_record

            return PipelineRunResult(
                migration_id=final_record.migration_id,
                migration_record=final_record,
                assurance_report=assurance_report,
            )

        candidate_sql = trans_res.response.target_sql
        tgt_analysis = AnalyzerService.analyze(candidate_sql)

        # STEP 3: Phase 3 Execution — DuckDB Execution Sandbox
        logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 3/8: Phase 3 DuckDB Execution Sandbox")
        src_exec = ExecutionService.execute(
            ExecutionRequest(
                sql=source_sql,
                dialect=source_dialect,
                dataset_id=dataset_id,
                execution_mode=ExecutionMode.SOURCE,
                migration_id=migration_id,
            )
        )
        tgt_exec = ExecutionService.execute(
            ExecutionRequest(
                sql=candidate_sql,
                dialect=target_dialect,
                dataset_id=dataset_id,
                execution_mode=ExecutionMode.TARGET,
                migration_id=migration_id,
            )
        )
        src_exec.migration_id = migration_id
        tgt_exec.migration_id = migration_id

        # Update dataset_hash on record once execution sandbox resolves it
        migration_record.dataset_hash = src_exec.dataset_hash

        # STRICT LIFECYCLE CHECK: If execution failed, do NOT proceed to validation
        if src_exec.status != ExecutionStatus.SUCCESS or tgt_exec.status != ExecutionStatus.SUCCESS:
            logger.warning(
                f"[MigrationOrchestrator] [{migration_id}] Execution failed (source={src_exec.status}, target={tgt_exec.status}). "
                f"Halting pipeline execution. Downstream validation will NOT be run."
            )
            assurance_report = self._assurance_service.evaluate_assurance(
                migration_id=migration_id,
                translation_result=trans_res,
                source_execution=src_exec,
                target_execution=tgt_exec,
                validation_report=None,
                discrepancy_report=None,
                diagnosis_ai_result=None,
                repair_verification_result=None,
            )
            assurance_report.metadata["profile"] = request.profile
            updated_record = self._assurance_service.get_migration(migration_id)
            final_record = updated_record if updated_record else migration_record

            return PipelineRunResult(
                migration_id=final_record.migration_id,
                migration_record=final_record,
                assurance_report=assurance_report,
            )

        # STEP 4: Phase 4 Validation — Multi-layer Semantic Validation
        logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 4/8: Phase 4 Multi-Layer Semantic Validation")
        val_report = ValidationService.validate_executions(
            source_execution_id=src_exec.execution_id,
            target_execution_id=tgt_exec.execution_id,
        )
        val_report.migration_id = migration_id

        # STEP 5: Phase 5 Diagnosis — Discrepancy Classification & Evidence
        disc_report = None
        diag_ai_res = None
        ver_res = None

        if val_report.overall_status != "PASS":
            logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 5/8: Phase 5 Discrepancy Classification")
            orchestrator = DiagnosisOrchestrator()
            disc_report = orchestrator.diagnose(
                report=val_report,
                source_analysis=src_analysis,
                target_analysis=tgt_analysis,
                total_output_rows=src_exec.row_count,
            )
            if disc_report:
                disc_report.migration_id = migration_id

            # STEP 6: Phase 7 AI Diagnosis & Repair Proposal (if discrepancies exist)
            if disc_report and disc_report.discrepancies:
                logger.info(
                    f"[MigrationOrchestrator] [{migration_id}] Step 6/8: Phase 7 AI Diagnosis & Repair ({len(disc_report.discrepancies)} discrepancies found)"
                )
                primary_disc = disc_report.discrepancies[0]
                category_str = primary_disc.category.value if hasattr(primary_disc.category, "value") else str(primary_disc.category)
                severity_str = primary_disc.severity.value if hasattr(primary_disc.severity, "value") else str(primary_disc.severity)
                diag_ai_res = DiagnosisAIService.diagnose_discrepancy(
                    discrepancy_id=primary_disc.discrepancy_id,
                    category=category_str,
                    severity=severity_str,
                    source_sql=source_sql,
                    target_sql=candidate_sql,
                    source_dialect=source_dialect,
                    target_dialect=target_dialect,
                    source_expression=primary_disc.source_expression or None,
                    target_expression=primary_disc.target_expression or None,
                    affected_row_count=primary_disc.affected_row_count,
                    affected_percentage=primary_disc.affected_percentage,
                    affected_columns=primary_disc.affected_output_columns,
                    validation_id=val_report.validation_id,
                    translation_id=trans_res.metadata.translation_id,
                    mock_mode=request.mock_mode,
                )
                if diag_ai_res:
                    diag_ai_res.migration_id = migration_id

                # STEP 7: Phase 8 Repair Verification (if repair proposed)
                if diag_ai_res and diag_ai_res.repair_proposal and diag_ai_res.repair_proposal.proposed_sql:
                    logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 7/8: Phase 8 Repair Execution & Deterministic Re-Validation")
                    ver_res = RepairVerificationService.verify_repair(
                        repair_id=diag_ai_res.repair_proposal.repair_id,
                        discrepancy_id=primary_disc.discrepancy_id,
                        target_dialect=target_dialect,
                        validation_report_before=val_report,
                        source_execution=src_exec,
                    )
                    if ver_res:
                        ver_res.migration_id = migration_id
        else:
            logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 5–7: Skipped (0 discrepancies detected, validation PASS)")

        # STEP 8: Phase 9 Migration Assurance & Quality Gate Evaluation
        logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 8/8: Phase 9 Migration Assurance & Gate Evaluation")
        assurance_report = self._assurance_service.evaluate_assurance(
            migration_id=migration_id,
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
        updated_record = self._assurance_service.get_migration(migration_id)
        final_record = updated_record if updated_record else migration_record

        logger.info(
            f"[MigrationOrchestrator] Completed migration {final_record.migration_id}: Status={final_record.final_status}, Score={final_record.assurance_score}"
        )

        return PipelineRunResult(
            migration_id=final_record.migration_id,
            migration_record=final_record,
            assurance_report=assurance_report,
        )
