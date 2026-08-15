"""Phase 10.1 Generic Migration Orchestrator Pydantic Data Models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.assurance.models import MigrationAssuranceReport, MigrationRecord


class PipelineRunRequest(BaseModel):
    """Input specification for dynamic end-to-end migration pipeline run."""

    source_sql: str = Field(..., description="Source SQL text to translate and migrate")
    source_dialect: str = Field(default="teradata", description="Source SQL dialect")
    target_dialect: str = Field(default="bigquery", description="Target SQL dialect")
    dataset_id: str = Field(default="customer_risk", description="Target execution dataset ID")
    profile: str = Field(default="dev", description="Data generation profile (dev, test, prod)")
    mock_mode: str | None = Field(default=None, description="Optional mock mode override for tests/demos")
    migration_id: str | None = Field(default=None, description="Optional explicit migration ID override")


class PipelineRunResult(BaseModel):
    """Result returned by MigrationOrchestrator."""

    migration_id: str
    migration_record: MigrationRecord
    assurance_report: MigrationAssuranceReport
