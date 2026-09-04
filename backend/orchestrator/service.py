"""Phase 10.1 Generic Migration Orchestrator Service.

Orchestrates Phase 1 through Phase 9 into a unified, end-to-end migration pipeline.
"""

from __future__ import annotations

import hashlib
from typing import Any

from backend.analyzer.service import AnalyzerService
from backend.assurance.service import MigrationAssuranceService
from backend.assurance.models import MigrationFinalStatus
from backend.core.logging import get_logger
from backend.diagnosis.orchestrator import DiagnosisOrchestrator
from backend.diagnosis_ai.service import DiagnosisAIService
from backend.execution.models import ExecutionMode, ExecutionRequest, ExecutionStatus
from backend.execution.service import ExecutionService
from backend.orchestrator.models import PipelineRunRequest, PipelineRunResult
from backend.preflight.validator import SchemaPreflightValidator
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

    def preflight_check(self, source_sql: str, dataset_id: str, source_dialect: str = "teradata") -> dict[str, Any]:
        """Perform preflight validation check for SQL & dataset compatibility."""
        from backend.datasets.registry import DatasetRegistry

        registry = DatasetRegistry()
        if not registry.exists(dataset_id):
            raise ValueError(f"DATASET_NOT_FOUND: Dataset '{dataset_id}' is not registered.")

        # Parse SQL syntax with AnalyzerService
        src_analysis = AnalyzerService.analyze(source_sql, dialect=source_dialect)

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
        self.preflight_check(source_sql, dataset_id, source_dialect=source_dialect)

        # STEP 0.5: Generate root identity & create MigrationRecord(CREATED) early
        import uuid
        from pathlib import Path
        
        migration_id = request.migration_id or f"MIG-{uuid.uuid4().hex[:12].upper()}"
        source_hash = hashlib.sha256(source_sql.encode()).hexdigest()[:16]
        
        # STEP 1: Phase 1 Analyzer — Analyze Source SQL AST & semantics (Moved up for canonical hashing)
        logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 1/8: Phase 1 Analyzer")
        src_analysis = AnalyzerService.analyze(source_sql, dialect=source_dialect)
        normalized_hash = src_analysis.sql_hash

        sql_bytes = source_sql.encode('utf-8')
        # 512KB Threshold
        if len(sql_bytes) > 512 * 1024:
            artifacts_dir = Path("backend/storage/artifacts")
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            artifact_path = artifacts_dir / f"{migration_id}_source.sql"
            artifact_path.write_bytes(sql_bytes)
            
            source_sql_val = None
            source_sql_storage = "artifact"
            source_sql_ref = str(artifact_path)
        else:
            source_sql_val = source_sql
            source_sql_storage = "database"
            source_sql_ref = None

        logger.info(
            f"[MigrationOrchestrator] [{migration_id}] Starting run (source_hash: {source_hash}, dialect: {source_dialect} -> {target_dialect}, dataset: {dataset_id})"
        )

        migration_record = self._assurance_service.get_migration(migration_id)
        if not migration_record:
            migration_record = self._assurance_service.create_migration(
                migration_id=migration_id,
                source_dialect=source_dialect,
                target_dialect=target_dialect,
                source_sql_hash=source_hash,
                normalized_sql_hash=normalized_hash,
                source_sql=source_sql_val,
                source_sql_storage=source_sql_storage,
                source_sql_ref=source_sql_ref,
                dataset_id=dataset_id,
                dataset_hash="pending",
            )
            
        from backend.assurance.service import get_active_source_candidate, create_source_candidate_version, save_source_candidate

        # STEP 1.1: Resolve Active Source Candidate
        active_src_cand = get_active_source_candidate(migration_id)
        if not active_src_cand:
            active_src_cand = create_source_candidate_version(
                migration_id=migration_id, 
                sql_text=source_sql_val or source_sql, 
                origin="ORIGINAL", 
                dialect=source_dialect
            )
            
        # STEP 1.5: Source Preflight Validation
        logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 1.5: Source Preflight Validation")
        src_preflight = SchemaPreflightValidator.validate(active_src_cand.sql_text, dataset_id, dialect=source_dialect)
        active_src_cand.preflight_summary = src_preflight
        active_src_cand.preflight_status = src_preflight.status
        save_source_candidate(active_src_cand)
        
        if not src_preflight.execution_allowed:
            logger.warning(
                f"[MigrationOrchestrator] [{migration_id}] Source schema preflight failed: {src_preflight.reason}. Halting pipeline."
            )
            # Create a partial assurance report reflecting the preflight failure
            assurance_report = self._assurance_service.evaluate_assurance(
                migration_id=migration_id,
                translation_result=None,
                preflight_summary=None,
                source_execution=None,
                target_execution=None,
                validation_report=None,
                discrepancy_report=None,
                diagnosis_ai_result=None,
                repair_verification_result=None,
                source_preflight_summary=src_preflight, # We will add this to evaluate_assurance
            )
            assurance_report.metadata["profile"] = request.profile
            # Force status to BLOCKED due to schema mismatch
            assurance_report.final_status = MigrationFinalStatus.BLOCKED
            assurance_report.decision_reason = src_preflight.reason or "Input source schema mismatch detected."
            
            # Save the report with the updated BLOCKED status
            self._assurance_service._repository.save_assurance_report(assurance_report)
            
            from backend.db.database import get_db_session
            from backend.db.models import MigrationRecordModel
            db = get_db_session()
            try:
                db.query(MigrationRecordModel).filter(MigrationRecordModel.migration_id == migration_id).update({"final_status": "BLOCKED"})
                db.commit()
            finally:
                db.close()
                
            updated_record = self._assurance_service.get_migration(migration_id)
            final_record = updated_record if updated_record else migration_record

            return PipelineRunResult(
                migration_id=final_record.migration_id,
                migration_record=final_record,
                assurance_report=assurance_report,
            )

        # (Analyzer already ran above to generate canonical hash)

        # STEP 2: Phase 6 Translator — AI/Rule-based Translation
        logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 2/8: Phase 6 AI Translator")
        
        from backend.datasets.registry import DatasetRegistry
        from backend.translator.models import SchemaContext, TableSchema, ColumnSchemaDef
        registry = DatasetRegistry()
        dataset = registry.get_dataset(dataset_id)
        schema_context = None
        if dataset:
            tables = []
            for t in dataset.table_summaries:
                cols = [ColumnSchemaDef(name=c.name, type=c.data_type) for c in t.columns]
                tables.append(TableSchema(name=t.table_name, columns=cols))
            schema_context = SchemaContext(tables=tables)
            
        trans_req = TranslationRequest(
            source_sql=active_src_cand.sql_text,
            source_dialect=source_dialect,
            target_dialect=target_dialect,
            dataset_id=dataset_id,
            migration_id=migration_id,
            schema_context=schema_context,
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
        tgt_analysis = AnalyzerService.analyze(candidate_sql, dialect=target_dialect)


        # STEP 2.2: Create Candidate Version
        from backend.assurance.service import create_candidate_version, save_candidate
        
        candidate = create_candidate_version(
            migration_id=migration_id,
            sql_text=candidate_sql,
            source="AI",
            parent_version_id=None
        )
        candidate.source_candidate_id = active_src_cand.candidate_id

        # STEP 2.5: Schema Preflight
        logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 2.5: Schema Preflight Validation")
        preflight_summary = SchemaPreflightValidator.validate(candidate_sql, dataset_id, dialect=target_dialect)
        
        candidate.preflight_summary = preflight_summary
        candidate.preflight_status = preflight_summary.status
        save_candidate(candidate)
        
        if not preflight_summary.execution_allowed:
            logger.warning(
                f"[MigrationOrchestrator] [{migration_id}] Schema preflight failed: {preflight_summary.reason}. Halting pipeline."
            )
            # Create a partial assurance report reflecting the preflight failure
            assurance_report = self._assurance_service.evaluate_assurance(
                migration_id=migration_id,
                translation_result=trans_res,
                preflight_summary=preflight_summary,
                source_execution=None,
                target_execution=None,
                validation_report=None,
                discrepancy_report=None,
                diagnosis_ai_result=None,
                repair_verification_result=None,
            )
            assurance_report.metadata["profile"] = request.profile
            # Force status to BLOCKED due to schema mismatch
            assurance_report.final_status = MigrationFinalStatus.BLOCKED
            assurance_report.decision_reason = preflight_summary.reason or "Input schema mismatch detected."
            
            # Save the report with the updated BLOCKED status
            self._assurance_service._repository.save_assurance_report(assurance_report)
            
            updated_record = self._assurance_service.get_migration(migration_id)
            # The background worker or service might need final_status updated directly too, though update_state doesn't set it immediately, it will be mapped.
            if updated_record:
                updated_record.final_status = MigrationFinalStatus.BLOCKED
                from backend.db.database import get_db_session
                from backend.db.models import MigrationRecordModel
                db = get_db_session()
                try:
                    db.query(MigrationRecordModel).filter(MigrationRecordModel.migration_id == migration_id).update({"final_status": "BLOCKED"})
                    db.commit()
                finally:
                    db.close()

            final_record = updated_record if updated_record else migration_record

            return PipelineRunResult(
                migration_id=final_record.migration_id,
                migration_record=final_record,
                assurance_report=assurance_report,
            )


        if preflight_summary.execution_allowed:
            return self.execute_migration(migration_id, profile=request.profile, translation_result=trans_res, mock_mode=request.mock_mode)
        else:
            # We already returned PipelineRunResult for blocked above
            pass

    def execute_migration(self, migration_id: str, profile: str | None = None, translation_result: Any | None = None, mock_mode: str | None = None) -> PipelineRunResult:
        '''Execute phases 3-9 for an already preflighted migration.'''
        from backend.assurance.service import get_active_candidate, get_active_source_candidate
        from backend.core.consistency_validator import CandidateStateError
        
        record = self._assurance_service.get_migration(migration_id)
        if not record:
            raise ValueError(f"Migration {migration_id} not found.")
            
        candidate = get_active_candidate(migration_id)
        if not candidate:
            raise CandidateStateError(f"No active candidate found for {migration_id}.")
            
        if not candidate.sql_text or not candidate.sql_text.strip():
            raise CandidateStateError(f"Active SQL candidate is missing or empty for {migration_id}.")
            
        if not candidate.preflight_status == "PASS" or not candidate.preflight_summary or not candidate.preflight_summary.execution_allowed:
            raise CandidateStateError(f"PRECONDITION_FAILED: Migration {migration_id} preflight is not PASS.")
            
        active_src = get_active_source_candidate(migration_id)
        if active_src:
            source_sql = active_src.sql_text
        elif record.source_sql_ref:
            from pathlib import Path
            ref_path = Path(record.source_sql_ref)
            if ref_path.exists():
                source_sql = ref_path.read_text(encoding="utf-8")
            else:
                raise CandidateStateError(
                    f"CANDIDATE_RESOLUTION_FAILED: Source SQL reference file not found "
                    f"for migration {migration_id}: {record.source_sql_ref}"
                )
        elif record.source_sql:
            source_sql = record.source_sql
        else:
            raise CandidateStateError(
                f"CANDIDATE_RESOLUTION_FAILED: No active source candidate, no source_sql_ref, "
                f"and no inline source_sql for migration {migration_id}. "
                f"Cannot determine which SQL to execute."
            )
            
        source_dialect = record.source_dialect
        target_dialect = record.target_dialect
        dataset_id = record.dataset_id
        candidate_sql = candidate.sql_text
        preflight_summary = candidate.preflight_summary
        
        # We need trans_res from the report to pass into evaluate_assurance.
        # But wait, evaluate_assurance expects it. We can get it from report.
        trans_res = translation_result
        report = self._assurance_service.get_assurance_report(migration_id)
        if not trans_res and report and report.translation_summary:
            from backend.translator.models import TranslationResult, TranslationMetadata, TranslationStatus
            trans_res = TranslationResult(
                metadata=TranslationMetadata(
                    translation_id=report.translation_summary.translation_id,
                    request_id="loaded",
                    provider=report.translation_summary.provider,
                    model=report.translation_summary.model,
                    source_dialect=source_dialect,
                    target_dialect=target_dialect,
                    source_sql_hash=record.source_sql_hash,
                    translation_context_hash="",
                    prompt_hash="",
                    created_at=report.translation_summary.created_at,
                ),
                status=getattr(TranslationStatus, report.translation_summary.status, TranslationStatus.SUCCESS),
                validation_summary="",
            )
            
        src_analysis = AnalyzerService.analyze(source_sql, dialect=source_dialect)
        tgt_analysis = AnalyzerService.analyze(candidate_sql, dialect=target_dialect)

        # STEP 3: Phase 3 Execution — DuckDB Execution Sandbox
        logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 3/8: Phase 3 DuckDB Execution Sandbox")
        src_exec = ExecutionService.execute(
            ExecutionRequest(
                sql=source_sql,
                dialect=source_dialect,
                dataset_id=dataset_id,
                execution_mode=ExecutionMode.SOURCE,
                migration_id=migration_id,
                candidate_id=candidate.candidate_id,
            )
        )
        tgt_exec = ExecutionService.execute(
            ExecutionRequest(
                sql=candidate_sql,
                dialect=target_dialect,
                dataset_id=dataset_id,
                execution_mode=ExecutionMode.TARGET,
                migration_id=migration_id,
                candidate_id=candidate.candidate_id,
            )
        )
        src_exec.migration_id = migration_id
        src_exec.candidate_id = candidate.candidate_id
        tgt_exec.migration_id = migration_id
        tgt_exec.candidate_id = candidate.candidate_id

        record.dataset_hash = src_exec.dataset_hash

        if src_exec.status != ExecutionStatus.SUCCESS or tgt_exec.status != ExecutionStatus.SUCCESS:
            src_unsupported = src_exec.status in (ExecutionStatus.SANDBOX_LIMITATION, ExecutionStatus.TARGET_CAPABILITY_UNSUPPORTED)
            tgt_unsupported = tgt_exec.status in (ExecutionStatus.SANDBOX_LIMITATION, ExecutionStatus.TARGET_CAPABILITY_UNSUPPORTED)
            if src_unsupported or tgt_unsupported:
                logger.warning(
                    f"[MigrationOrchestrator] [{migration_id}] Execution halted: sandbox lacks capability "
                    f"(source={src_exec.status.value}, target={tgt_exec.status.value}). "
                    f"Marking assurance INCONCLUSIVE."
                )
            else:
                logger.warning(
                    f"[MigrationOrchestrator] [{migration_id}] Execution failed "
                    f"(source={src_exec.status.value}, target={tgt_exec.status.value}). "
                    f"Halting pipeline."
                )
            assurance_report = self._assurance_service.evaluate_assurance(
                migration_id=migration_id,
                translation_result=trans_res,
                preflight_summary=preflight_summary,
                source_execution=src_exec,
                target_execution=tgt_exec,
                validation_report=None,
                discrepancy_report=None,
                diagnosis_ai_result=None,
                repair_verification_result=None,
                candidate_id=candidate.candidate_id,
            )
            if profile: assurance_report.metadata["profile"] = profile
            updated_record = self._assurance_service.get_migration(migration_id)
            final_record = updated_record if updated_record else record
            return PipelineRunResult(migration_id=final_record.migration_id, migration_record=final_record, assurance_report=assurance_report)

        # STEP 4: Phase 4 Validation
        logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 4/8: Phase 4 Multi-Layer Semantic Validation")
        val_report = ValidationService.validate_executions(
            source_execution_id=src_exec.execution_id,
            target_execution_id=tgt_exec.execution_id,
        )
        val_report.migration_id = migration_id
        val_report.candidate_id = candidate.candidate_id

        # STEP 5: Phase 5 Diagnosis
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

            if disc_report and disc_report.discrepancies:
                logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 6/8: Phase 7 AI Diagnosis & Repair")
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
                    translation_id=trans_res.metadata.translation_id if trans_res else "",
                    mock_mode=mock_mode,
                )
                if diag_ai_res:
                    diag_ai_res.migration_id = migration_id

                if diag_ai_res and diag_ai_res.repair_proposal and diag_ai_res.repair_proposal.proposed_sql:
                    logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 7/8: Phase 8 Repair Execution")
                    ver_res = RepairVerificationService.verify_repair(
                        repair_id=diag_ai_res.repair_proposal.repair_id,
                        discrepancy_id=primary_disc.discrepancy_id,
                        target_dialect=target_dialect,
                        validation_report_before=val_report,
                        source_execution=src_exec,
                    )
                    if ver_res:
                        ver_res.migration_id = migration_id

        # STEP 8: Phase 9 Migration Assurance
        logger.info(f"[MigrationOrchestrator] [{migration_id}] Step 8/8: Phase 9 Migration Assurance & Gate Evaluation")
        assurance_report = self._assurance_service.evaluate_assurance(
            migration_id=migration_id,
            translation_result=trans_res,
            preflight_summary=preflight_summary,
            source_execution=src_exec,
            target_execution=tgt_exec,
            validation_report=val_report,
            discrepancy_report=disc_report,
            diagnosis_ai_result=diag_ai_res,
            repair_verification_result=ver_res,
            candidate_id=candidate.candidate_id,
        )
        if profile: assurance_report.metadata["profile"] = profile
        updated_record = self._assurance_service.get_migration(migration_id)
        final_record = updated_record if updated_record else record
        return PipelineRunResult(migration_id=final_record.migration_id, migration_record=final_record, assurance_report=assurance_report)
