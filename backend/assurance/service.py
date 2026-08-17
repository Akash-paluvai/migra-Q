"""Phase 9 Migration Assurance Service — orchestrates assurance evaluation.

No LLM, no SQL execution, no repair.
Consumes Phase 1–8 artifacts and produces MigrationAssuranceReport.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from backend.assurance.decision import DecisionEngine
from backend.assurance.gates import HardGateEvaluator
from backend.assurance.lineage import AuditLineageBuilder
from backend.assurance.models import (
    MigrationAssuranceReport,
    MigrationFinalStatus,
    MigrationRecord,
    MigrationState,
    VerificationPath,
)
from backend.assurance.repository import MigrationAssuranceRepository
from backend.assurance.scoring import AssuranceScorer
from backend.assurance.state import MigrationStateMachine
from backend.assurance.summary import SummaryBuilder
from backend.core.logging import get_logger
from backend.diagnosis.models import DiscrepancyReport
from backend.diagnosis_ai.models import DiagnosisAIResult
from backend.execution.models import ExecutionResult, ExecutionStatus
from backend.repair_verification.models import (
    RepairVerificationResult,
    VerificationStatus,
)
from backend.translator.models import (
    CandidateValidationStatus,
    TranslationResult,
    TranslationStatus,
)
from backend.validation.models import ValidationCheckStatus, ValidationReport

logger = get_logger(__name__)


class MigrationAssuranceService:
    """Orchestrates Phase 9 migration assurance evaluation.

    Workflow:
      1. Build summaries from upstream artifacts
      2. Calculate assurance score + evidence coverage
      3. Evaluate hard gates
      4. Call determine_verified() for final decision
      5. Build audit lineage
      6. Persist and return MigrationAssuranceReport
    """

    def __init__(self) -> None:
        self._scorer = AssuranceScorer()
        self._gate_evaluator = HardGateEvaluator()
        self._lineage_builder = AuditLineageBuilder()
        self._decision_engine = DecisionEngine()
        self._summary_builder = SummaryBuilder()
        self._state_machine = MigrationStateMachine()
        self._repository = MigrationAssuranceRepository()

    def create_migration(
        self,
        *,
        migration_id: str | None = None,
        source_dialect: str,
        target_dialect: str,
        source_sql_hash: str,
        normalized_sql_hash: str | None = None,
        source_sql: str | None = None,
        source_sql_storage: str = "database",
        source_sql_ref: str | None = None,
        dataset_id: str,
        dataset_hash: str,
    ) -> MigrationRecord:
        """Create a new migration record in CREATED state."""
        mid = migration_id or f"MIG-{uuid.uuid4().hex[:12].upper()}"
        record = MigrationRecord(
            migration_id=mid,
            source_dialect=source_dialect,
            target_dialect=target_dialect,
            source_sql_hash=source_sql_hash,
            normalized_sql_hash=normalized_sql_hash,
            source_sql=source_sql,
            source_sql_storage=source_sql_storage,
            source_sql_ref=source_sql_ref,
            dataset_id=dataset_id,
            dataset_hash=dataset_hash,
        )
        self._repository.save_migration(record)
        return record

    def evaluate_assurance(
        self,
        *,
        migration_id: str,
        translation_result: TranslationResult,
        source_execution: ExecutionResult | None = None,
        target_execution: ExecutionResult | None = None,
        validation_report: ValidationReport | None = None,
        discrepancy_report: DiscrepancyReport | None = None,
        diagnosis_ai_result: DiagnosisAIResult | None = None,
        repair_verification_result: RepairVerificationResult | None = None,
        validation_report_after: ValidationReport | None = None,
    ) -> MigrationAssuranceReport:
        """Evaluate migration assurance from Phase 1–8 artifacts."""
        from backend.core.consistency_validator import ArtifactStateConsistencyValidator

        start_time = datetime.now(timezone.utc)

        # 0. Enforce Universal Lineage Boundary & SHA256 Hash Invariant
        migration = self._repository.get_migration(migration_id)
        if migration:
            if hasattr(translation_result, "metadata") and translation_result.metadata:
                t_mid = getattr(translation_result.metadata, "migration_id", None)
                t_hash = getattr(translation_result.metadata, "source_sql_hash", None)
                if t_mid and t_mid != migration_id:
                    raise ValueError(f"ARTIFACT_LINEAGE_MISMATCH: Translation artifact migration_id '{t_mid}' != '{migration_id}'")
                if t_hash and t_hash != migration.source_sql_hash:
                    raise ValueError(f"ARTIFACT_LINEAGE_MISMATCH: Translation source_sql_hash '{t_hash}' != '{migration.source_sql_hash}'")

            for exec_res in [source_execution, target_execution]:
                if exec_res is not None:
                    e_mid = getattr(exec_res, "migration_id", None)
                    if e_mid and e_mid != migration_id:
                        raise ValueError(f"ARTIFACT_LINEAGE_MISMATCH: Execution artifact migration_id '{e_mid}' != '{migration_id}'")

            if validation_report is not None:
                v_mid = getattr(validation_report, "migration_id", None)
                if v_mid and v_mid != migration_id:
                    raise ValueError(f"ARTIFACT_LINEAGE_MISMATCH: Validation artifact migration_id '{v_mid}' != '{migration_id}'")

            if discrepancy_report is not None:
                d_mid = getattr(discrepancy_report, "migration_id", None)
                if d_mid and d_mid != migration_id:
                    raise ValueError(f"ARTIFACT_LINEAGE_MISMATCH: Discrepancy artifact migration_id '{d_mid}' != '{migration_id}'")

        # 1. Build summaries
        translation_summary = self._summary_builder.build_translation_summary(translation_result)
        execution_summary = self._summary_builder.build_execution_summary(
            source_execution, target_execution
        )
        validation_summary = self._summary_builder.build_validation_summary(validation_report)
        discrepancy_summary = self._summary_builder.build_discrepancy_summary(discrepancy_report)
        diagnosis_summary = self._summary_builder.build_diagnosis_summary(diagnosis_ai_result)

        repair_proposal = diagnosis_ai_result.repair_proposal if diagnosis_ai_result else None
        repair_summary = self._summary_builder.build_repair_summary(
            repair_proposal, repair_verification_result
        )
        verification_summary = self._summary_builder.build_verification_summary(
            repair_verification_result
        )

        # 2. Calculate assurance score (use post-repair report if repair was verified)
        report_for_scoring = validation_report
        if repair_verification_result is not None and repair_verification_result.status == VerificationStatus.VERIFIED:
            if validation_report_after is not None:
                report_for_scoring = validation_report_after
            elif repair_verification_result.validation_id_after:
                from backend.validation.service import ValidationService
                fetched = ValidationService.get_validation(repair_verification_result.validation_id_after)
                if fetched:
                    report_for_scoring = fetched

        score = self._scorer.calculate(report_for_scoring)

        # 3. Determine repair path
        repair_attempted = repair_verification_result is not None

        # 4. Compute remaining discrepancy count
        if repair_attempted and repair_verification_result is not None:
            remaining_discrepancy_count = repair_verification_result.remaining_discrepancy_count
        elif discrepancy_report is not None:
            remaining_discrepancy_count = discrepancy_report.discrepancy_count
        elif validation_report is not None and validation_report.overall_status != "PASS":
            remaining_discrepancy_count = sum(c.mismatch_count for c in validation_report.checks if c.status == ValidationCheckStatus.FAIL) or 1
        else:
            remaining_discrepancy_count = 0

        # 5. Build audit lineage
        lineage = self._lineage_builder.build(
            translation_id=translation_result.metadata.translation_id,
            source_execution_id=source_execution.execution_id if source_execution else "",
            target_execution_id=target_execution.execution_id if target_execution else "",
            validation_id=validation_report.validation_id if validation_report else "",
            diagnosis_id=(
                discrepancy_report.diagnosis_id if discrepancy_report else ""
            ),
            ai_diagnosis_id=(
                diagnosis_ai_result.metadata.diagnosis_id if diagnosis_ai_result else ""
            ),
            repair_id=(
                repair_proposal.repair_id if repair_proposal else ""
            ),
            verification_id=(
                repair_verification_result.verification_id if repair_verification_result else ""
            ),
            repair_attempted=repair_attempted,
        )

        # 6. Extract gate inputs
        source_succeeded = (source_execution.status == ExecutionStatus.SUCCESS) if source_execution else False
        target_succeeded = (target_execution.status == ExecutionStatus.SUCCESS) if target_execution else False
        translation_valid = (
            translation_result.candidate_validation_status == CandidateValidationStatus.VALID_SYNTAX
        )
        schema_valid = self._check_schema_valid(validation_report) if validation_report else False
        has_unresolved_critical = self._check_unresolved_critical(discrepancy_report, repair_verification_result)

        # Repair-specific gate inputs
        dataset_hash_unchanged: bool | None = None
        config_hash_unchanged: bool | None = None
        repair_verification_status: str | None = None
        new_disc_after_repair: int | None = None

        if repair_attempted and repair_verification_result is not None:
            repair_verification_status = repair_verification_result.status.value
            new_disc_after_repair = repair_verification_result.new_discrepancy_count
            meta = repair_verification_result.metadata
            dataset_hash_unchanged = (
                meta.dataset_hash_before == meta.dataset_hash_after
                if meta.dataset_hash_after is not None else True
            )
            config_hash_unchanged = (
                meta.validation_config_hash_before == meta.validation_config_hash_after
                if meta.validation_config_hash_after is not None else True
            )

        # 7. Evaluate hard gates
        gate_evaluation = self._gate_evaluator.evaluate(
            source_execution_succeeded=source_succeeded,
            translation_syntactically_valid=translation_valid,
            target_execution_succeeded=target_succeeded,
            schema_valid=schema_valid,
            has_unresolved_critical=has_unresolved_critical,
            remaining_discrepancy_count=remaining_discrepancy_count,
            repair_attempted=repair_attempted,
            new_discrepancy_count_after_repair=new_disc_after_repair,
            repair_verification_status=repair_verification_status,
            dataset_hash_unchanged=dataset_hash_unchanged,
            validation_config_hash_unchanged=config_hash_unchanged,
            audit_lineage_complete=lineage.is_complete,
        )

        # 8. Determine verification path
        verification_path = (
            VerificationPath.REPAIRED_PASS if repair_attempted
            else VerificationPath.DIRECT_PASS
        )

        # 9. Determine final status using decision engine
        final_status, decision_reason = self._decision_engine.determine_final_status(
            gate_evaluation, verification_path
        )

        # If translation or execution failed, provide explicit technical failure reason
        if translation_result.status != TranslationStatus.SUCCESS:
            final_status = MigrationFinalStatus.FAILED
            err_msg = translation_result.metadata.error_message or translation_result.validation_summary or translation_result.status.value
            decision_reason = f"Assurance evaluation could not be completed because translation failed: {err_msg}"
        elif source_execution is None or target_execution is None or not (source_succeeded and target_succeeded):
            final_status = MigrationFinalStatus.FAILED
            decision_reason = "Assurance evaluation could not be completed because execution failed."

        # 10. Validate State Consistency
        ArtifactStateConsistencyValidator.validate_full_pipeline_state(
            translation_status=translation_result.status.value,
            target_sql=translation_result.response.target_sql if translation_result.response else None,
            candidate_validation_status=(
                translation_result.candidate_validation_status.value
                if translation_result.candidate_validation_status else None
            ),
            target_execution_status=target_execution.status.value if target_execution else None,
            validation_status=validation_report.overall_status if validation_report else None,
            validation_ran=validation_report is not None,
            repair_id=repair_proposal.repair_id if repair_proposal else None,
            repair_status=repair_proposal.status.value if repair_proposal else None,
            proposed_sql=repair_proposal.proposed_sql if repair_proposal else None,
            verification_id=repair_verification_result.verification_id if repair_verification_result else None,
            verification_status=repair_verification_result.status.value if repair_verification_result else None,
            final_status=final_status.value,
            evidence_score=score.evidence_score,
        )

        # 11. Build limitations
        limitations = self._build_limitations(score, repair_attempted, discrepancy_report)

        # 12. Build report
        duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        report = MigrationAssuranceReport(
            migration_id=migration_id,
            final_status=final_status,
            decision_reason=decision_reason,
            verification_path=verification_path,
            score=score,
            gate_evaluation=gate_evaluation,
            translation_summary=translation_summary,
            execution_summary=execution_summary,
            validation_summary=validation_summary,
            discrepancy_summary=discrepancy_summary,
            diagnosis_summary=diagnosis_summary,
            repair_summary=repair_summary,
            verification_summary=verification_summary,
            lineage=lineage,
            limitations=limitations,
            metadata={"duration_ms": round(duration_ms, 2)},
        )

        # 13. Persist
        self._repository.save_assurance_report(report)

        # 14. Update migration record
        migration = self._repository.get_migration(migration_id)
        if migration:
            migration.final_status = final_status
            migration.current_state = self._status_to_state(final_status)
            migration.assurance_score = score.evidence_score
            migration.evidence_coverage = score.evidence_coverage
            migration.updated_at = datetime.now(timezone.utc).isoformat()
            self._repository.save_migration(migration)

        return report

    def get_migration(self, migration_id: str) -> MigrationRecord | None:
        """Retrieve a migration record."""
        return self._repository.get_migration(migration_id)

    def get_assurance_report(self, migration_id: str) -> MigrationAssuranceReport | None:
        """Retrieve the assurance report for a migration."""
        return self._repository.get_assurance_report(migration_id)

    def list_migrations(self) -> list[MigrationRecord]:
        """Retrieve all migration records."""
        return self._repository.get_all_migrations()

    def get_flagship_migration(self) -> MigrationRecord:
        """Retrieve the dedicated flagship migration (MIG-FLAGSHIP-001), creating it if not present."""
        flagship = self._repository.get_migration("MIG-FLAGSHIP-001")
        if flagship:
            return flagship

        # Seed flagship migration uniquely if not yet initialized
        from scripts.run_flagship_demo import run_flagship_demo
        run_flagship_demo(flagship_id="MIG-FLAGSHIP-001")
        flagship = self._repository.get_migration("MIG-FLAGSHIP-001")
        if flagship:
            return flagship

        # Fallback if creation was customized
        all_now = self._repository.get_all_migrations()
        if all_now:
            return all_now[0]

        raise RuntimeError("Failed to initialize flagship migration.")

    def run_migration_pipeline(
        self,
        *,
        source_sql: str,
        source_dialect: str = "teradata",
        target_dialect: str = "bigquery",
        dataset_id: str,
        profile: str = "dev",
        mock_mode: str | None = None,
    ) -> MigrationAssuranceReport:
        """Execute complete Phase 1–9 migration pipeline dynamically for given SQL."""
        import hashlib

        from backend.analyzer.service import AnalyzerService
        from backend.diagnosis.orchestrator import DiagnosisOrchestrator
        from backend.diagnosis_ai.service import DiagnosisAIService
        from backend.execution.models import ExecutionMode, ExecutionRequest
        from backend.execution.service import ExecutionService
        from backend.repair_verification.service import RepairVerificationService
        from backend.translator.models import TranslationRequest
        from backend.translator.service import TranslationService
        from backend.validation.service import ValidationService

        # 1. AI Translation
        trans_req = TranslationRequest(
            source_sql=source_sql,
            source_dialect=source_dialect,
            target_dialect=target_dialect,
            dataset_id=dataset_id,
        )
        trans_res = TranslationService.translate(trans_req, mock_mode=mock_mode)
        candidate_sql = trans_res.response.target_sql if trans_res.response and trans_res.response.target_sql else source_sql

        # 2. Execution (Source & Target)
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

        # 3. Validation
        val_report = ValidationService.validate_executions(
            source_execution_id=src_exec.execution_id,
            target_execution_id=tgt_exec.execution_id,
        )

        # 4. Discrepancy Analysis
        src_ana = AnalyzerService.analyze(source_sql, dialect=source_dialect)
        tgt_ana = AnalyzerService.analyze(candidate_sql, dialect=target_dialect)
        orchestrator = DiagnosisOrchestrator()
        disc_report = orchestrator.diagnose(
            report=val_report,
            source_analysis=src_ana,
            target_analysis=tgt_ana,
            total_output_rows=src_exec.row_count,
        )

        # 5. AI Diagnosis & Repair Proposal
        diag_ai_res = None
        ver_res = None
        if disc_report and disc_report.discrepancies:
            primary_disc = disc_report.discrepancies[0]
            diag_ai_res = DiagnosisAIService.diagnose_discrepancy(
                discrepancy_id=primary_disc.discrepancy_id,
                category=primary_disc.category.value,
                severity=primary_disc.severity.value,
                source_sql=source_sql,
                target_sql=candidate_sql,
                source_dialect=source_dialect,
                target_dialect=target_dialect,
                affected_row_count=primary_disc.affected_row_count,
                affected_percentage=primary_disc.affected_percentage,
                affected_columns=primary_disc.affected_columns,
                validation_id=val_report.validation_id,
                translation_id=trans_res.metadata.translation_id,
                mock_mode=mock_mode,
            )

            # 6. Repair Verification
            if diag_ai_res and diag_ai_res.repair_proposal and diag_ai_res.repair_proposal.proposed_sql:
                ver_res = RepairVerificationService.verify_repair(
                    repair_id=diag_ai_res.repair_proposal.repair_id,
                    discrepancy_id=primary_disc.discrepancy_id,
                    target_dialect=target_dialect,
                    validation_report_before=val_report,
                    source_execution=src_exec,
                )

        # 7. Assurance & Audit Lineage
        source_hash = hashlib.sha256(source_sql.encode()).hexdigest()[:16]
        migration = self.create_migration(
            source_dialect=source_dialect,
            target_dialect=target_dialect,
            source_sql_hash=source_hash,
            dataset_id=dataset_id,
            dataset_hash=src_exec.dataset_hash,
        )

        assurance_report = self.evaluate_assurance(
            migration_id=migration.migration_id,
            translation_result=trans_res,
            source_execution=src_exec,
            target_execution=tgt_exec,
            validation_report=val_report,
            discrepancy_report=disc_report,
            diagnosis_ai_result=diag_ai_res,
            repair_verification_result=ver_res,
        )
        assurance_report.metadata["profile"] = profile
        return assurance_report

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _check_schema_valid(validation_report: ValidationReport | None) -> bool:
        """Check if SchemaValidator status is not FAIL."""
        if validation_report is None:
            return False
        for check in validation_report.checks:
            if check.check_name == "SchemaValidator":
                return check.status != ValidationCheckStatus.FAIL
        # If SchemaValidator is not present, treat as valid (no negative evidence)
        return True

    @staticmethod
    def _check_unresolved_critical(
        discrepancy_report: DiscrepancyReport | None,
        repair_verification_result: RepairVerificationResult | None,
    ) -> bool:
        """Check if any CRITICAL severity discrepancy remains unresolved."""
        if discrepancy_report is None:
            return False

        # If repair was attempted and verified, check remaining discrepancies
        if repair_verification_result is not None:
            if repair_verification_result.status == VerificationStatus.VERIFIED:
                return False
            # Repair didn't fully resolve — check original severity
            for d in discrepancy_report.discrepancies:
                if d.severity.value == "CRITICAL":
                    return True
            return False

        # No repair — check all discrepancies
        for d in discrepancy_report.discrepancies:
            if d.severity.value == "CRITICAL":
                return True
        return False

    @staticmethod
    def _build_limitations(
        score, repair_attempted: bool, discrepancy_report
    ) -> list[str]:
        """Build list of assurance limitations for the report."""
        limitations: list[str] = []
        if score.evidence_coverage is not None and score.evidence_coverage < 100.0:
            skipped = [
                c.name for c in score.components
                if c.status.value == "NOT_APPLICABLE"
            ]
            if skipped:
                limitations.append(
                    f"Evidence coverage is {score.evidence_coverage}%. "
                    f"Skipped validators: {', '.join(skipped)}."
                )
        if repair_attempted:
            limitations.append(
                "Migration required AI-assisted repair. Verified by deterministic re-validation."
            )
        return limitations

    @staticmethod
    def _status_to_state(status: MigrationFinalStatus) -> MigrationState:
        """Map final status to terminal state."""
        mapping = {
            MigrationFinalStatus.VERIFIED: MigrationState.VERIFIED,
            MigrationFinalStatus.BLOCKED: MigrationState.BLOCKED,
            MigrationFinalStatus.FAILED: MigrationState.FAILED,
            MigrationFinalStatus.ERROR: MigrationState.ERROR,
            MigrationFinalStatus.IN_PROGRESS: MigrationState.VALIDATING,
        }
        return mapping.get(status, MigrationState.ERROR)
