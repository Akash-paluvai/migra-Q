"""Phase 9 & 10 Migration Assurance & Management API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.assurance.models import MigrationAssuranceReport, MigrationRecord
from backend.assurance.service import MigrationAssuranceService

assurance_router = APIRouter(prefix="/api/v1/migrations", tags=["assurance"])

_service = MigrationAssuranceService()


class MigrationRunRequest(BaseModel):
    source_sql: str
    source_dialect: str = "teradata"
    target_dialect: str = "bigquery"
    dataset_id: str = "customer_risk"


@assurance_router.get("")
def list_migrations() -> list[MigrationRecord]:
    """Get all migration records."""
    # Ensure flagship migration exists if list is empty
    migrations = _service.list_migrations()
    if not migrations:
        _service.get_flagship_migration()
        migrations = _service.list_migrations()
    return migrations


@assurance_router.get("/flagship")
def get_flagship_migration() -> MigrationRecord:
    """Retrieve latest flagship migration (retrieval shortcut)."""
    try:
        return _service.get_flagship_migration()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@assurance_router.post("/run")
def run_migration(req: MigrationRunRequest) -> MigrationRecord:
    """Trigger a new migration workflow run dynamically for user SQL & parameters."""
    report = _service.run_migration_pipeline(
        source_sql=req.source_sql,
        source_dialect=req.source_dialect,
        target_dialect=req.target_dialect,
        dataset_id=req.dataset_id,
    )
    record = _service.get_migration(report.migration_id)
    if record is None:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve created migration record {report.migration_id}"
        )
    return record


@assurance_router.get("/{migration_id}")
def get_migration(migration_id: str) -> MigrationRecord:
    """Get migration record by ID."""
    if migration_id == "flagship":
        return get_flagship_migration()
    record = _service.get_migration(migration_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Migration {migration_id} not found")
    return record


@assurance_router.get("/{migration_id}/assurance")
def get_assurance_report(migration_id: str) -> MigrationAssuranceReport:
    """Get the full assurance report for a migration."""
    if migration_id == "flagship":
        flg = _service.get_flagship_migration()
        migration_id = flg.migration_id
    report = _service.get_assurance_report(migration_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail=f"Assurance report for migration {migration_id} not found",
        )
    return report


@assurance_router.get("/{migration_id}/lineage")
def get_lineage(migration_id: str) -> dict:
    """Get audit lineage for a migration."""
    if migration_id == "flagship":
        flg = _service.get_flagship_migration()
        migration_id = flg.migration_id
    report = _service.get_assurance_report(migration_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail=f"Assurance report for migration {migration_id} not found",
        )
    return report.lineage.model_dump()


@assurance_router.get("/{migration_id}/events")
def get_events(migration_id: str) -> list:
    """Get state transition events for a migration."""
    if migration_id == "flagship":
        flg = _service.get_flagship_migration()
        migration_id = flg.migration_id
    events = _service.get_events(migration_id)
    return [e.model_dump() for e in events]


@assurance_router.get("/{migration_id}/artifacts")
def get_artifacts(migration_id: str) -> dict[str, Any]:
    """Get map of all phase artifact summaries for a migration."""
    if migration_id == "flagship":
        flg = _service.get_flagship_migration()
        migration_id = flg.migration_id
    report = _service.get_assurance_report(migration_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail=f"Assurance report for migration {migration_id} not found",
        )
    return {
        "translation": report.translation_summary.model_dump() if report.translation_summary else None,
        "execution": report.execution_summary.model_dump() if report.execution_summary else None,
        "validation": report.validation_summary.model_dump() if report.validation_summary else None,
        "discrepancy": report.discrepancy_summary.model_dump() if report.discrepancy_summary else None,
        "diagnosis": report.diagnosis_summary.model_dump() if report.diagnosis_summary else None,
        "repair": report.repair_summary.model_dump() if report.repair_summary else None,
        "verification": report.verification_summary.model_dump() if report.verification_summary else None,
        "lineage": report.lineage.model_dump(),
    }
