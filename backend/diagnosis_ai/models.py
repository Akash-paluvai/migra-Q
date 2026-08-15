"""Pydantic domain models for Phase 7 AI Diagnosis & Repair Proposal Engine."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DiagnosisStatus(str, Enum):
    """Status of AI diagnosis."""

    DIAGNOSED = "DIAGNOSED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    FAILED = "FAILED"


class RepairStatus(str, Enum):
    """Status of AI candidate repair proposal."""

    PROPOSED = "PROPOSED"
    NO_REPAIR = "NO_REPAIR"
    FAILED = "FAILED"


class EvidenceItem(BaseModel):
    """Single stable evidence item in the EvidencePack (e.g. E-001, E-002)."""

    evidence_id: str
    evidence_type: str
    description: str
    details: dict[str, Any] = Field(default_factory=dict)


class EvidencePack(BaseModel):
    """Deterministic, bounded evidence payload supplied to the LLM."""

    discrepancy_id: str
    category: str
    severity: str
    classification_confidence: float = 1.0
    source_expression: str | None = None
    target_expression: str | None = None
    analysis_path: str | None = None
    affected_row_count: int = 0
    affected_percentage: float = 0.0
    affected_columns: list[str] = Field(default_factory=list)
    items: list[EvidenceItem] = Field(default_factory=list)
    structural_differences: list[str] = Field(default_factory=list)
    representative_examples: list[dict[str, Any]] = Field(default_factory=list)


class GroundedClaim(BaseModel):
    """Structured claim object referencing specific evidence IDs."""

    text: str
    evidence_refs: list[str] = Field(default_factory=list)


class AIDiagnosis(BaseModel):
    """Structured AI diagnosis model."""

    diagnosis_id: str
    discrepancy_id: str
    status: DiagnosisStatus
    observed_change: str
    likely_mechanism: str
    possible_cause: str
    uncertainty: str
    claims: list[GroundedClaim] = Field(default_factory=list)
    diagnosis_confidence: float = 0.0


class RepairChange(BaseModel):
    """Structured patch change item."""

    location: str
    before_expression: str
    after_expression: str
    change_type: str = "MODIFY"


class RepairProposal(BaseModel):
    """Candidate repair proposal model (PROPOSED candidate only, requiring Phase 8 re-validation)."""

    repair_id: str
    discrepancy_id: str
    status: RepairStatus
    original_sql: str
    proposed_sql: str
    changed_region: str
    changes: list[RepairChange] = Field(default_factory=list)
    rationale: str
    expected_effect: str
    claims: list[GroundedClaim] = Field(default_factory=list)
    constraints_checked: list[str] = Field(default_factory=list)
    repair_confidence: float = 0.0


class DiagnosisAIResponse(BaseModel):
    """Structured LLM output model returned by provider."""

    observed_change: str
    likely_mechanism: str
    possible_cause: str
    uncertainty: str
    diagnosis_claims: list[GroundedClaim] = Field(default_factory=list)
    proposed_sql: str | None = None
    changed_region: str | None = None
    changes: list[RepairChange] = Field(default_factory=list)
    repair_rationale: str | None = None
    expected_effect: str | None = None
    repair_claims: list[GroundedClaim] = Field(default_factory=list)


class DiagnosisContext(BaseModel):
    """Complete context container built deterministically from upstream Phase 1-6 artifacts."""

    discrepancy_id: str
    validation_id: str
    translation_id: str
    source_sql: str
    target_sql: str
    source_dialect: str
    target_dialect: str
    evidence_pack: EvidencePack
    context_hash: str


class DiagnosisAIMetadata(BaseModel):
    """Metadata tracking provider execution, hashes, and token metrics."""

    diagnosis_id: str
    discrepancy_id: str
    provider: str
    model: str
    context_hash: str
    prompt_hash: str
    created_at: str
    duration_ms: float = 0.0
    retry_count: int = 0
    input_token_count: int | None = None
    output_token_count: int | None = None
    total_token_count: int | None = None
    error_code: str | None = None
    error_message: str | None = None
    diagnosis_ai_version: str = "0.1.0"
    prompt_version: str = "0.1.0"


class DiagnosisAIResult(BaseModel):
    """Top-level Phase 7 result artifact containing diagnosis and repair proposal."""

    metadata: DiagnosisAIMetadata
    diagnosis: AIDiagnosis
    repair_proposal: RepairProposal
