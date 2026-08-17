"""Pydantic domain models for Phase 8 Repair Execution & Deterministic Re-Validation Engine."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

VERIFICATION_ENGINE_VERSION = "1.0.0"


class VerificationStatus(str, Enum):
    """Deterministic status of candidate repair verification."""

    VERIFIED = "VERIFIED"
    FAILED_VERIFICATION = "FAILED_VERIFICATION"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
    NEW_DISCREPANCIES = "NEW_DISCREPANCIES"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    CANDIDATE_REJECTED = "CANDIDATE_REJECTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class DiscrepancyOutcomeStatus(str, Enum):
    """Outcome for a specific discrepancy comparison between BEFORE and AFTER."""

    RESOLVED = "RESOLVED"
    PERSISTS = "PERSISTS"
    CHANGED = "CHANGED"
    UNABLE_TO_MATCH = "UNABLE_TO_MATCH"


class VerificationEvidenceItem(BaseModel):
    """Structured evidence item supporting repair verification decision."""

    evidence_id: str
    evidence_type: str
    description: str
    details: dict[str, Any] = Field(default_factory=dict)


class DiscrepancyOutcome(BaseModel):
    """Detailed outcome comparison for an individual discrepancy."""

    discrepancy_id_before: str
    category: str
    analysis_path: str | None = None
    affected_region: str | None = None
    status: DiscrepancyOutcomeStatus
    affected_rows_before: int | None = None
    affected_rows_after: int | None = None
    reduction_count: int | None = None
    reduction_percentage: float = 0.0
    matching_after_discrepancy_ids: list[str] = Field(default_factory=list)
    new_discrepancy_ids: list[str] = Field(default_factory=list)
    summary: str = ""


class RepairOutcome(BaseModel):
    """Aggregated outcome for targeted repair proposal."""

    discrepancy_id_before: str
    status: DiscrepancyOutcomeStatus
    affected_rows_before: int | None = None
    affected_rows_after: int | None = None
    reduction_count: int | None = None
    reduction_percentage: float = 0.0
    matching_after_discrepancy_ids: list[str] = Field(default_factory=list)
    new_discrepancy_ids: list[str] = Field(default_factory=list)
    evidence: list[VerificationEvidenceItem] = Field(default_factory=list)
    summary: str = ""


class VerificationMetadata(BaseModel):
    """Metadata describing the verification run environment and hashes."""

    verification_id: str
    repair_id: str
    discrepancy_id: str
    validation_id_before: str
    validation_id_after: str | None = None
    execution_id_before: str
    execution_id_repaired: str | None = None
    dataset_id: str
    dataset_hash_before: str
    dataset_hash_after: str | None = None
    validation_config_hash_before: str
    validation_config_hash_after: str | None = None
    target_dialect: str = "bigquery"
    verification_version: str = VERIFICATION_ENGINE_VERSION
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_ms: float = 0.0
    persistence_status: str = "PERSISTED"
    rejection_reason: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class RepairVerificationResult(BaseModel):
    """Complete, immutable Phase 8 repair verification result artifact."""

    verification_id: str
    migration_id: str | None = None
    repair_id: str
    discrepancy_id: str
    validation_id_before: str
    validation_id_after: str | None = None
    execution_id_before: str
    execution_id_repaired: str | None = None
    status: VerificationStatus
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verification_version: str = VERIFICATION_ENGINE_VERSION
    original_discrepancy_count: int = 0
    remaining_discrepancy_count: int = 0
    new_discrepancy_count: int = 0
    resolved_discrepancy_count: int = 0
    affected_rows_before: int | None = None
    affected_rows_after: int | None = None
    affected_percentage_before: float = 0.0
    affected_percentage_after: float = 0.0
    reduction_count: int = 0
    reduction_percentage: float = 0.0
    before_report_reference: str = ""
    after_report_reference: str = ""
    original_target_sql: str = ""
    repaired_target_sql: str = ""
    resolved_discrepancies: list[str] = Field(default_factory=list)
    remaining_discrepancies: list[str] = Field(default_factory=list)
    new_discrepancies: list[str] = Field(default_factory=list)
    outcomes: list[RepairOutcome] = Field(default_factory=list)
    evidence: list[VerificationEvidenceItem] = Field(default_factory=list)
    execution_metadata: dict[str, Any] = Field(default_factory=dict)
    metadata: VerificationMetadata
    summary: str = ""
