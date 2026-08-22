"""Summary builders — produce reference-only summaries for each phase artifact."""

from __future__ import annotations

from backend.assurance.models import (
    DiagnosisSummary,
    DiscrepancySummary,
    ExecutionSummary,
    RepairSummary,
    TranslationSummary,
    ValidationCheckSummary,
    ValidationSummary,
    VerificationSummary,
)
from backend.diagnosis.models import DiscrepancyReport
from backend.diagnosis_ai.models import DiagnosisAIResult, RepairProposal
from backend.execution.models import ExecutionResult
from backend.repair_verification.models import RepairVerificationResult
from backend.translator.models import TranslationResult
from backend.validation.models import ValidationReport


class SummaryBuilder:
    """Builds Phase 9 summary models from upstream Phase 1–8 artifacts.

    Each method produces a reference-only summary — no full artifact content is embedded.
    """

    def build_translation_summary(self, translation_result: TranslationResult) -> TranslationSummary:
        """Build a TranslationSummary from Phase 6 TranslationResult."""
        return TranslationSummary(
            translation_id=translation_result.metadata.translation_id,
            source_dialect=translation_result.metadata.source_dialect,
            target_dialect=translation_result.metadata.target_dialect,
            status=translation_result.status.value,
            candidate_validation_status=(
                translation_result.candidate_validation_status.value
                if translation_result.candidate_validation_status else None
            ),
            source_sql_hash=getattr(translation_result.metadata, "source_sql_hash", ""),
            candidate_sql=getattr(translation_result.response, "target_sql", ""),
            provider=translation_result.metadata.provider,
            model=translation_result.metadata.model,
            created_at=translation_result.metadata.created_at,
            transformations=[t.model_dump() for t in translation_result.transformations],
            transformation_count=translation_result.transformation_count,
            assumption_count=translation_result.assumption_count,
        )

    def build_execution_summary(
        self,
        source: ExecutionResult | None,
        target: ExecutionResult | None,
    ) -> ExecutionSummary | None:
        """Build an ExecutionSummary from Phase 3 source and target ExecutionResults."""
        if source is None or target is None:
            return None
        return ExecutionSummary(
            source_execution_id=source.execution_id,
            target_execution_id=target.execution_id,
            source_status=source.status.value,
            target_status=target.status.value,
            source_row_count=source.row_count,
            target_row_count=target.row_count,
            dataset_id=source.dataset_id,
            dataset_hash=source.dataset_hash,
        )

    def build_validation_summary(self, report: ValidationReport | None) -> ValidationSummary | None:
        """Build a ValidationSummary from Phase 4 ValidationReport."""
        if report is None:
            return None
        checks = [
            ValidationCheckSummary(
                check_name=c.check_name,
                status=c.status.value,
                score=c.score,
                mismatch_count=c.mismatch_count,
            )
            for c in report.checks
        ]
        return ValidationSummary(
            validation_id=report.validation_id,
            overall_status=report.overall_status,
            checks=checks,
        )

    def build_discrepancy_summary(
        self, report: DiscrepancyReport | None
    ) -> DiscrepancySummary:
        """Build a DiscrepancySummary from Phase 5 DiscrepancyReport."""
        if report is None:
            return DiscrepancySummary()
        total_affected = sum((d.affected_row_count or 0) for d in report.discrepancies)
        return DiscrepancySummary(
            diagnosis_id=report.diagnosis_id,
            discrepancy_count=report.discrepancy_count,
            category_counts=dict(report.category_counts),
            severity_counts=dict(report.severity_counts),
            total_affected_rows=total_affected,
        )

    def build_diagnosis_summary(
        self, result: DiagnosisAIResult | None
    ) -> DiagnosisSummary:
        """Build a DiagnosisSummary from Phase 7 DiagnosisAIResult."""
        if result is None:
            return DiagnosisSummary()
        return DiagnosisSummary(
            diagnosis_id=result.metadata.diagnosis_id,
            discrepancy_id=result.diagnosis.discrepancy_id,
            status=result.diagnosis.status.value,
            observed_change=result.diagnosis.observed_change,
            diagnosis_confidence=result.diagnosis.diagnosis_confidence,
        )

    def build_repair_summary(
        self,
        proposal: RepairProposal | None,
        verification: RepairVerificationResult | None = None,
    ) -> RepairSummary:
        """Build a RepairSummary from Phase 7 RepairProposal."""
        if proposal is None:
            return RepairSummary()
        return RepairSummary(
            repair_id=proposal.repair_id,
            status=proposal.status.value,
            repair_confidence=proposal.repair_confidence,
            changed_region=proposal.changed_region,
            original_sql=proposal.original_sql or "",
            proposed_sql=proposal.proposed_sql or "",
        )

    def build_verification_summary(
        self, result: RepairVerificationResult | None, reason: str | None = None
    ) -> VerificationSummary:
        """Build a VerificationSummary from Phase 8 RepairVerificationResult."""
        if result is None:
            return VerificationSummary(
                verification_id=None,
                status="NOT_EXECUTED",
                reason=reason or "Verification was not executed.",
            )
        return VerificationSummary(
            verification_id=result.verification_id,
            status=result.status.value,
            original_discrepancy_count=result.original_discrepancy_count,
            remaining_discrepancy_count=result.remaining_discrepancy_count,
            new_discrepancy_count=result.new_discrepancy_count,
            resolved_discrepancy_count=result.resolved_discrepancy_count,
            affected_rows_before=result.affected_rows_before,
            affected_rows_after=result.affected_rows_after,
            reduction_percentage=result.reduction_percentage,
        )
