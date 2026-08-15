"""RepairVerificationContext — immutable container holding BEFORE and AFTER artifacts for Phase 8."""

from __future__ import annotations

from dataclasses import dataclass

from backend.analyzer.models import SQLAnalysis
from backend.diagnosis.models import DiscrepancyReport
from backend.diagnosis_ai.models import AIDiagnosis, RepairProposal
from backend.execution.models import ExecutionResult
from backend.validation.models import ValidationConfig, ValidationReport


@dataclass(frozen=True)
class RepairVerificationContext:
    """Immutable data container encapsulating all state and artifacts for repair verification."""

    repair_proposal: RepairProposal
    ai_diagnosis: AIDiagnosis
    source_execution: ExecutionResult
    target_execution_before: ExecutionResult
    validation_report_before: ValidationReport
    discrepancy_report_before: DiscrepancyReport
    source_analysis: SQLAnalysis | None = None
    target_analysis_before: SQLAnalysis | None = None
    validation_config: ValidationConfig | None = None
    target_execution_repaired: ExecutionResult | None = None
    validation_report_after: ValidationReport | None = None
    discrepancy_report_after: DiscrepancyReport | None = None
    target_analysis_repaired: SQLAnalysis | None = None

    @property
    def dataset_id(self) -> str:
        return self.source_execution.dataset_id

    @property
    def dataset_hash_before(self) -> str:
        return self.source_execution.dataset_hash

    @property
    def dataset_hash_after(self) -> str | None:
        if self.target_execution_repaired:
            return self.target_execution_repaired.dataset_hash
        return None

    @property
    def original_target_sql(self) -> str:
        return self.repair_proposal.original_sql

    @property
    def proposed_sql(self) -> str:
        return self.repair_proposal.proposed_sql

    @property
    def target_dialect(self) -> str:
        if self.target_execution_before.metadata and "dialect" in self.target_execution_before.metadata:
            return str(self.target_execution_before.metadata["dialect"])
        return "bigquery"
