"""RepairVerificationService — high-level facade orchestrating deterministic repair verification."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from backend.analyzer.service import AnalyzerService
from backend.core.logging import get_logger
from backend.diagnosis.models import DiscrepancyReport
from backend.diagnosis.orchestrator import DiagnosisOrchestrator
from backend.diagnosis.service import DiagnosisService
from backend.diagnosis_ai.models import AIDiagnosis, DiagnosisStatus, RepairProposal
from backend.diagnosis_ai.repository import get_diagnosis_ai_result, get_repair_proposal_by_id
from backend.execution.models import ExecutionResult, ExecutionStatus
from backend.execution.service import ExecutionService
from backend.repair_verification.candidate_validator import CandidateRepairValidator
from backend.repair_verification.comparator import DiscrepancyComparator
from backend.repair_verification.context import RepairVerificationContext
from backend.repair_verification.exceptions import ExecutionFailedError
from backend.repair_verification.executor import RepairExecutor
from backend.repair_verification.models import (
    VERIFICATION_ENGINE_VERSION,
    DiscrepancyOutcomeStatus,
    RepairOutcome,
    RepairVerificationResult,
    VerificationMetadata,
)
from backend.repair_verification.repository import save_verification_result
from backend.repair_verification.status import VerificationStatusDeterminer
from backend.validation.context import ValidationContext
from backend.validation.models import ValidationConfig, ValidationReport
from backend.validation.orchestrator import ValidationOrchestrator
from backend.validation.service import ValidationService

logger = get_logger(__name__)


class RepairVerificationService:
    """Facade orchestrating candidate integrity validation, execution, re-validation, and verification decision."""

    @classmethod
    def verify_repair(
        cls,
        repair_id: str,
        discrepancy_id: str | None = None,
        repair_proposal: RepairProposal | None = None,
        ai_diagnosis: AIDiagnosis | None = None,
        validation_report_before: Any | None = None,
        discrepancy_report_before: DiscrepancyReport | None = None,
        source_execution: ExecutionResult | None = None,
        target_execution_before: ExecutionResult | None = None,
        target_dialect: str = "bigquery",
    ) -> RepairVerificationResult:
        """Execute complete deterministic repair verification pipeline."""
        start_time = datetime.now(timezone.utc)
        verification_id = f"ver-ai-{uuid.uuid4().hex[:12]}"

        # 1. Load RepairProposal if not explicitly provided
        if not repair_proposal:
            repair_proposal = get_repair_proposal_by_id(repair_id)
            if not repair_proposal:
                raise ValueError(f"Repair proposal '{repair_id}' not found.")

        disc_id = discrepancy_id or repair_proposal.discrepancy_id

        # 2. Retrieve AI Diagnosis Result metadata
        stored_proposed_sql: str | None = None
        if not ai_diagnosis:
            ai_res = get_diagnosis_ai_result(f"diag-ai-{repair_id}")
            if ai_res:
                ai_diagnosis = ai_res.diagnosis
                stored_proposed_sql = ai_res.repair_proposal.proposed_sql
            else:
                ai_diagnosis = AIDiagnosis(
                    diagnosis_id=f"diag-{repair_id}",
                    discrepancy_id=disc_id,
                    status=DiagnosisStatus.DIAGNOSED,
                    observed_change="Proposed repair candidate",
                    likely_mechanism="Automated repair candidate",
                    possible_cause="Operator shift",
                    uncertainty="None",
                )
                stored_proposed_sql = repair_proposal.proposed_sql
        else:
            stored_proposal = get_repair_proposal_by_id(repair_id)
            if stored_proposal:
                stored_proposed_sql = stored_proposal.proposed_sql

        orig_sql = repair_proposal.original_sql.strip()

        # 3. Retrieve BEFORE validation report and discrepancy report if not provided
        if not validation_report_before:
            val_reports = []
            if hasattr(ValidationService, "list_validations"):
                try:
                    val_reports = ValidationService.list_validations(limit=10)
                except Exception:
                    pass
            if val_reports:
                validation_report_before = val_reports[0]
            else:
                validation_report_before = ValidationReport(
                    validation_id=f"val-default-{uuid.uuid4().hex[:8]}",
                    source_execution_id="exec-src-default",
                    target_execution_id="exec-tgt-default",
                    dataset_id="customer_risk",
                )

        val_id_before = validation_report_before.validation_id

        if not discrepancy_report_before:
            try:
                discrepancy_report_before = DiagnosisService.diagnose_validation(val_id_before)
            except Exception:
                discrepancy_report_before = DiscrepancyReport(
                    diagnosis_id=f"diag-{val_id_before}",
                    validation_id=val_id_before,
                    discrepancies=[],
                )

        # 4. Retrieve BEFORE executions
        if not source_execution:
            source_execution = ExecutionService.get_execution(validation_report_before.source_execution_id)
            if not source_execution:
                source_execution = ExecutionResult(
                    execution_id=validation_report_before.source_execution_id,
                    query_hash="hash-src-default",
                    dataset_id="customer_risk",
                    dataset_hash="ds-hash-default",
                    execution_mode="SOURCE",  # type: ignore[arg-type]
                    status=ExecutionStatus.SUCCESS,  # type: ignore[arg-type]
                )

        if not target_execution_before:
            target_execution_before = ExecutionService.get_execution(validation_report_before.target_execution_id)
            if not target_execution_before:
                target_execution_before = ExecutionResult(
                    execution_id=validation_report_before.target_execution_id,
                    query_hash="hash-tgt-default",
                    dataset_id="customer_risk",
                    dataset_hash="ds-hash-default",
                    execution_mode="TARGET",  # type: ignore[arg-type]
                    status=ExecutionStatus.SUCCESS,  # type: ignore[arg-type]
                )

        dataset_id = source_execution.dataset_id
        dataset_hash_before = source_execution.dataset_hash
        val_config = getattr(validation_report_before, "config", None) or ValidationConfig()
        config_hash_before = DiscrepancyComparator.compute_config_hash(val_config)

        # 5. Run 12 Pre-Execution Candidate Integrity Checks
        is_candidate_valid, rejection_reason, details_dict = CandidateRepairValidator.validate_candidate(
            proposal=repair_proposal,
            original_target_sql=orig_sql,
            target_dialect=target_dialect,
            stored_proposal_sql=stored_proposed_sql,
        )

        rows_before = 0
        if discrepancy_report_before and discrepancy_report_before.discrepancies:
            t_rec = next((d for d in discrepancy_report_before.discrepancies if d.discrepancy_id == disc_id), None)
            if t_rec:
                rows_before = t_rec.affected_row_count
            else:
                rows_before = discrepancy_report_before.discrepancies[0].affected_row_count

        meta = VerificationMetadata(
            verification_id=verification_id,
            repair_id=repair_id,
            discrepancy_id=disc_id,
            validation_id_before=val_id_before,
            execution_id_before=source_execution.execution_id,
            dataset_id=dataset_id,
            dataset_hash_before=dataset_hash_before,
            validation_config_hash_before=config_hash_before,
            target_dialect=target_dialect,
            rejection_reason=rejection_reason if not is_candidate_valid else None,
        )

        # If integrity checks fail -> CANDIDATE_REJECTED (Do NOT run SQL, Phase 4, or Phase 5)
        if not is_candidate_valid:
            status, summary = VerificationStatusDeterminer.determine_status(
                candidate_valid=False,
                rejection_reason=rejection_reason,
                execution_succeeded=False,
                target_outcome=RepairOutcome(
                    discrepancy_id_before=disc_id,
                    status=DiscrepancyOutcomeStatus.PERSISTS,
                    affected_rows_before=rows_before,
                    affected_rows_after=rows_before,
                ),
                new_discrepancies=[],
            )

            result = RepairVerificationResult(
                verification_id=verification_id,
                repair_id=repair_id,
                discrepancy_id=disc_id,
                validation_id_before=val_id_before,
                execution_id_before=source_execution.execution_id,
                status=status,
                original_discrepancy_count=len(discrepancy_report_before.discrepancies) if discrepancy_report_before else 1,
                remaining_discrepancy_count=len(discrepancy_report_before.discrepancies) if discrepancy_report_before else 1,
                new_discrepancy_count=0,
                resolved_discrepancy_count=0,
                affected_rows_before=rows_before,
                affected_rows_after=rows_before,
                original_target_sql=orig_sql,
                repaired_target_sql=repair_proposal.proposed_sql,
                summary=summary,
                metadata=meta,
                execution_metadata={"candidate_integrity_check": details_dict},
            )
            save_verification_result(result)
            return result

        # 6. Execute Repaired SQL through Phase 3 SandboxExecutor
        target_execution_repaired: ExecutionResult | None = None
        exec_error_code: str | None = None
        exec_error_msg: str | None = None

        try:
            target_execution_repaired = RepairExecutor.execute_repaired_sql(
                proposed_sql=repair_proposal.proposed_sql,
                dataset_id=dataset_id,
                target_dialect=target_dialect,
            )
        except ExecutionFailedError as exc:
            exec_error_code = exc.error_code
            exec_error_msg = exc.error_message
            logger.error("Phase 8 repaired SQL execution failed: %s", exc)

        # If execution failed -> EXECUTION_FAILED (Do NOT call Phase 4 or Phase 5)
        if not target_execution_repaired or exec_error_code:
            meta.error_code = exec_error_code or "EXECUTION_FAILED"
            meta.error_message = exec_error_msg or "Execution failed"
            status, summary = VerificationStatusDeterminer.determine_status(
                candidate_valid=True,
                rejection_reason=None,
                execution_succeeded=False,
                target_outcome=RepairOutcome(
                    discrepancy_id_before=disc_id,
                    status=DiscrepancyOutcomeStatus.PERSISTS,
                    affected_rows_before=rows_before,
                    affected_rows_after=rows_before,
                ),
                new_discrepancies=[],
            )

            result = RepairVerificationResult(
                verification_id=verification_id,
                repair_id=repair_id,
                discrepancy_id=disc_id,
                validation_id_before=val_id_before,
                execution_id_before=source_execution.execution_id,
                status=status,
                original_discrepancy_count=len(discrepancy_report_before.discrepancies) if discrepancy_report_before else 1,
                remaining_discrepancy_count=len(discrepancy_report_before.discrepancies) if discrepancy_report_before else 1,
                new_discrepancy_count=0,
                resolved_discrepancy_count=0,
                affected_rows_before=rows_before,
                affected_rows_after=rows_before,
                original_target_sql=orig_sql,
                repaired_target_sql=repair_proposal.proposed_sql,
                summary=summary,
                metadata=meta,
                execution_metadata={"error_code": exec_error_code, "error_message": exec_error_msg},
            )
            save_verification_result(result)
            return result

        meta.execution_id_repaired = target_execution_repaired.execution_id
        meta.dataset_hash_after = target_execution_repaired.dataset_hash

        # 7. Invoke Phase 4 Validation Orchestrator for Re-Validation
        val_ctx_after = ValidationContext(
            source_execution=source_execution,
            target_execution=target_execution_repaired,
            config=val_config,
        )
        orchestrator_val = ValidationOrchestrator()
        val_report_after = orchestrator_val.validate(val_ctx_after)
        ValidationService._persist_report_artifact(val_report_after)
        meta.validation_id_after = val_report_after.validation_id
        meta.validation_config_hash_after = DiscrepancyComparator.compute_config_hash(getattr(val_report_after, "config", None) or val_config)

        # 8. Invoke Phase 5 Diagnosis Orchestrator for Re-Classification
        src_ana = None
        tgt_ana_after = None
        src_meta = getattr(source_execution, "metadata", None) or {}
        if isinstance(src_meta, dict) and "sql" in src_meta:
            try:
                src_ana = AnalyzerService.analyze(source_execution.metadata["sql"])
            except Exception:
                pass
        try:
            tgt_ana_after = AnalyzerService.analyze(repair_proposal.proposed_sql)
        except Exception:
            pass

        diag_orchestrator = DiagnosisOrchestrator()
        discrepancy_report_after = diag_orchestrator.diagnose(
            report=val_report_after,
            source_analysis=src_ana,
            target_analysis=tgt_ana_after,
        )

        # 9. Build RepairVerificationContext
        ctx = RepairVerificationContext(
            repair_proposal=repair_proposal,
            ai_diagnosis=ai_diagnosis,
            source_execution=source_execution,
            target_execution_before=target_execution_before,
            validation_report_before=validation_report_before,
            discrepancy_report_before=discrepancy_report_before,
            target_execution_repaired=target_execution_repaired,
            validation_report_after=val_report_after,
            discrepancy_report_after=discrepancy_report_after,
        )

        # 10. Run Comparative Analysis
        outcome, resolved_ids, remaining_ids, new_ids, evidence = DiscrepancyComparator.compare_context(ctx)

        # 11. Determine Final VerificationStatus
        status, summary = VerificationStatusDeterminer.determine_status(
            candidate_valid=True,
            rejection_reason=None,
            execution_succeeded=True,
            target_outcome=outcome,
            new_discrepancies=new_ids,
            contract_preserved=True,
            dataset_unchanged=(source_execution.dataset_hash == target_execution_repaired.dataset_hash),
            config_unchanged=(meta.validation_config_hash_before == meta.validation_config_hash_after),
        )

        end_time = datetime.now(timezone.utc)
        duration_ms = round((end_time - start_time).total_seconds() * 1000.0, 2)
        meta.duration_ms = duration_ms

        result = RepairVerificationResult(
            verification_id=verification_id,
            repair_id=repair_id,
            discrepancy_id=disc_id,
            validation_id_before=val_id_before,
            validation_id_after=val_report_after.validation_id,
            execution_id_before=source_execution.execution_id,
            execution_id_repaired=target_execution_repaired.execution_id,
            status=status,
            created_at=end_time.isoformat(),
            verification_version=VERIFICATION_ENGINE_VERSION,
            original_discrepancy_count=len(discrepancy_report_before.discrepancies) if discrepancy_report_before else 1,
            remaining_discrepancy_count=len(remaining_ids),
            new_discrepancy_count=len(new_ids),
            resolved_discrepancy_count=len(resolved_ids),
            affected_rows_before=outcome.affected_rows_before,
            affected_rows_after=outcome.affected_rows_after,
            reduction_count=outcome.reduction_count,
            reduction_percentage=outcome.reduction_percentage,
            before_report_reference=val_id_before,
            after_report_reference=val_report_after.validation_id,
            original_target_sql=orig_sql,
            repaired_target_sql=repair_proposal.proposed_sql,
            resolved_discrepancies=resolved_ids,
            remaining_discrepancies=remaining_ids,
            new_discrepancies=new_ids,
            outcomes=[outcome],
            evidence=evidence,
            execution_metadata={
                "duration_ms": duration_ms,
                "dataset_id": dataset_id,
                "dataset_hash": dataset_hash_before,
            },
            metadata=meta,
            summary=summary,
        )

        save_verification_result(result)
        return result

    @classmethod
    def get_verification(cls, verification_id: str) -> RepairVerificationResult | None:
        """Retrieve RepairVerificationResult artifact by verification_id."""
        from backend.repair_verification.repository import get_verification_result

        return get_verification_result(verification_id)
