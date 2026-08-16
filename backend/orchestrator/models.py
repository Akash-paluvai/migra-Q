"""Phase 10.2 Generic Migration Orchestrator Pydantic Data Models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.assurance.models import MigrationAssuranceReport, MigrationRecord


class PipelineRunRequest(BaseModel):
    """Input specification for dynamic end-to-end migration pipeline run."""

    source_sql: str = Field(..., description="Source SQL text to translate and migrate")
    source_dialect: str = Field(..., description="Source SQL dialect")
    target_dialect: str = Field(..., description="Target SQL dialect")
    dataset_id: str = Field(..., description="Target execution dataset ID")
    profile: str = Field(default="dev", description="Data generation profile (dev, test, prod)")
    mock_mode: str | None = Field(default=None, description="Optional mock mode override for tests/demos")
    migration_id: str | None = Field(default=None, description="Optional explicit migration ID override")


class MigrationRunResponse(BaseModel):
    """API Response returned after starting or running a migration workflow."""

    migration_id: str = Field(..., description="Unique migration identifier")
    current_state: str = Field(..., description="Current pipeline execution state (e.g. CREATED, TRANSLATED, VERIFIED, BLOCKED)")
    source_dialect: str = Field(..., description="Source SQL dialect")
    target_dialect: str = Field(..., description="Target SQL dialect")
    dataset_id: str = Field(..., description="Dataset ID used for execution sandbox")
    source_sql_hash: str = Field(..., description="SHA256 hash of submitted source SQL")


class PipelineRunResult(BaseModel):
    """Result returned by MigrationOrchestrator."""

    migration_id: str
    migration_record: MigrationRecord
    assurance_report: MigrationAssuranceReport
