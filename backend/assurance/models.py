"""Pydantic domain models for Phase 9 Migration Assurance & Audit Decision Layer."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from backend.assurance import ASSURANCE_VERSION

# ---------------------------------------------------------------------------
# Core Enums
# ---------------------------------------------------------------------------


class MigrationState(str, Enum):
    """Explicit migration state machine states."""

    CREATED = "CREATED"
    ANALYZING = "ANALYZING"
    TRANSLATING = "TRANSLATING"
    EXECUTING = "EXECUTING"
    VALIDATING = "VALIDATING"
    DISCREPANCIES_FOUND = "DISCREPANCIES_FOUND"
    DIAGNOSING = "DIAGNOSING"
    REPAIR_PROPOSED = "REPAIR_PROPOSED"
    REPAIR_VERIFYING = "REPAIR_VERIFYING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class MigrationFinalStatus(str, Enum):
    """Final deterministic status — no LLM influence."""

    VERIFIED = "VERIFIED"
    BLOCKED = "BLOCKED"
    BLOCKED_PROVIDER_LIMIT = "BLOCKED_PROVIDER_LIMIT"
    FAILED = "FAILED"
    IN_PROGRESS = "IN_PROGRESS"
    ERROR = "ERROR"


class VerificationPath(str, Enum):
    """How the migration reached its final status."""

    DIRECT_PASS = "DIRECT_PASS"
    REPAIRED_PASS = "REPAIRED_PASS"


class GateOutcome(str, Enum):
    """Outcome of a single hard gate evaluation.

    - PASS: the gate condition was satisfied.
    - FAIL: the gate condition was NOT satisfied.
    - NOT_APPLICABLE: the gate does not apply to this migration path
      (e.g. repair gates when no repair was attempted).
    """

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ComponentStatus(str, Enum):
    """Status of a score component.

    - SCORED: validator ran, score is meaningful.
    - NOT_APPLICABLE: validator was SKIPPED, excluded from denominator.
    - ERROR: validator errored, score is 0.
    """

    SCORED = "SCORED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ERROR = "ERROR"


class AssuranceBand(str, Enum):
    """Descriptive assurance band for reporting only — never overrides gates."""

    STRONG_EVIDENCE = "STRONG_EVIDENCE"          # 95–100
    MINOR_CONCERNS = "MINOR_CONCERNS"            # 85–94.99
    SIGNIFICANT_CONCERNS = "SIGNIFICANT_CONCERNS"  # 70–84.99
    POOR_ASSURANCE = "POOR_ASSURANCE"            # < 70


# ---------------------------------------------------------------------------
# Hard Gate Models
# ---------------------------------------------------------------------------


class HardGateResult(BaseModel):
    """Result of a single hard gate evaluation."""

    gate_id: str
    gate_name: str
    outcome: GateOutcome
    reason: str


class HardGateEvaluation(BaseModel):
    """Aggregated result of all hard gate evaluations."""

    gates: list[HardGateResult] = Field(default_factory=list)
    all_passed: bool = False
    total_gates: int = 0
    passed_count: int = 0
    failed_count: int = 0
    not_applicable_count: int = 0


# ---------------------------------------------------------------------------
# Score Models
# ---------------------------------------------------------------------------


class ScoreComponent(BaseModel):
    """Individual component of the assurance score."""

    name: str
    weight: float
    raw_score: float
    weighted_score: float
    effective_weight: float = 0.0
    status: ComponentStatus
    source_check: str


class AssuranceScore(BaseModel):
    """Complete assurance scoring result.

    evidence_score and evidence_coverage are None when validation evidence did not run.
    """

    evidence_score: float | None = None
    evidence_coverage: float | None = None
    band: AssuranceBand | None = None
    components: list[ScoreComponent] = Field(default_factory=list)



# ---------------------------------------------------------------------------
# Phase Summary Models
# ---------------------------------------------------------------------------


class TranslationSummary(BaseModel):
    """Aggregated Phase 6 translation summary."""

    translation_id: str
    source_dialect: str
    target_dialect: str
    status: str
    candidate_validation_status: str | None = None
    source_sql_hash: str = ""
    candidate_sql: str = ""
    provider: str = ""
    model: str = ""
    created_at: str = ""


class ExecutionSummary(BaseModel):
    """Aggregated Phase 3 execution summary."""

    source_execution_id: str
    target_execution_id: str
    source_status: str
    target_status: str
    source_row_count: int = 0
    target_row_count: int = 0
    dataset_id: str = ""
    dataset_hash: str = ""


class ValidationCheckSummary(BaseModel):
    """Summary of a single Phase 4 validation check."""

    check_name: str
    status: str
    score: float = 0.0
    mismatch_count: int = 0


class ValidationSummary(BaseModel):
    """Aggregated Phase 4 validation summary."""

    validation_id: str
    overall_status: str
    checks: list[ValidationCheckSummary] = Field(default_factory=list)


class DiscrepancySummary(BaseModel):
    """Aggregated Phase 5 discrepancy summary."""

    diagnosis_id: str = ""
    discrepancy_count: int = 0
    category_counts: dict[str, int] = Field(default_factory=dict)
    severity_counts: dict[str, int] = Field(default_factory=dict)
    total_affected_rows: int = 0


class DiagnosisSummary(BaseModel):
    """Aggregated Phase 7 AI diagnosis summary."""

    diagnosis_id: str = ""
    discrepancy_id: str = ""
    status: str = ""
    observed_change: str = ""
    diagnosis_confidence: float = 0.0


class RepairSummary(BaseModel):
    """Aggregated Phase 7/8 repair summary."""

    repair_id: str = ""
    status: str = ""
    repair_confidence: float = 0.0
    changed_region: str = ""
    original_sql: str = ""
    proposed_sql: str = ""


class VerificationSummary(BaseModel):
    """Aggregated Phase 8 verification summary."""

    verification_id: str = ""
    status: str = ""
    original_discrepancy_count: int = 0
    remaining_discrepancy_count: int = 0
    new_discrepancy_count: int = 0
    resolved_discrepancy_count: int = 0
    affected_rows_before: int = 0
    affected_rows_after: int = 0
    reduction_percentage: float = 0.0


# ---------------------------------------------------------------------------
# Audit Lineage
# ---------------------------------------------------------------------------


class AuditLineage(BaseModel):
    """Complete provenance chain linking all Phase 1–8 artifact IDs."""

    translation_id: str = ""
    source_execution_id: str = ""
    target_execution_id: str = ""
    validation_id: str = ""
    diagnosis_id: str = ""
    ai_diagnosis_id: str = ""
    repair_id: str = ""
    verification_id: str = ""
    verification_path: VerificationPath = VerificationPath.DIRECT_PASS
    is_complete: bool = False


# ---------------------------------------------------------------------------
# Migration Record & State Events
# ---------------------------------------------------------------------------


class MigrationRecord(BaseModel):
    """Migration-level record tracking state and assurance."""

    migration_id: str
    source_dialect: str
    target_dialect: str
    source_sql_hash: str
    normalized_sql_hash: str | None = None
    source_sql: str | None = None
    source_sql_storage: str = "database"
    source_sql_ref: str | None = None
    dataset_id: str
    dataset_hash: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    current_state: MigrationState = MigrationState.CREATED
    final_status: MigrationFinalStatus = MigrationFinalStatus.IN_PROGRESS
    assurance_score: float | None = None
    evidence_coverage: float | None = None
    assurance_version: str = ASSURANCE_VERSION


class MigrationStateEvent(BaseModel):
    """Immutable event recording a state transition."""

    migration_id: str
    from_state: MigrationState
    to_state: MigrationState
    reason: str
    artifact_id: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Migration Assurance Report
# ---------------------------------------------------------------------------


class MigrationAssuranceReport(BaseModel):
    """Complete Phase 9 migration assurance report.

    This is the top-level output artifact of Phase 9.
    """

    migration_id: str
    assurance_version: str = ASSURANCE_VERSION
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Final decision
    final_status: MigrationFinalStatus = MigrationFinalStatus.IN_PROGRESS
    decision_reason: str = ""
    verification_path: VerificationPath = VerificationPath.DIRECT_PASS

    # Score (describes evidence, does NOT determine decision)
    score: AssuranceScore = Field(default_factory=AssuranceScore)

    # Hard gates (determine decision)
    gate_evaluation: HardGateEvaluation = Field(default_factory=HardGateEvaluation)

    # Phase summaries
    translation_summary: TranslationSummary | None = None
    execution_summary: ExecutionSummary | None = None
    validation_summary: ValidationSummary | None = None
    discrepancy_summary: DiscrepancySummary | None = None
    diagnosis_summary: DiagnosisSummary | None = None
    repair_summary: RepairSummary | None = None
    verification_summary: VerificationSummary | None = None

    # Audit lineage
    lineage: AuditLineage = Field(default_factory=AuditLineage)

    # Limitations & metadata
    limitations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
