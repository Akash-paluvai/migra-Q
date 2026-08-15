"""Phase 9 Assurance API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.assurance.models import MigrationAssuranceReport, MigrationRecord
from backend.assurance.service import MigrationAssuranceService

assurance_router = APIRouter(prefix="/api/v1/migrations", tags=["assurance"])

_service = MigrationAssuranceService()


@assurance_router.get("/{migration_id}")
def get_migration(migration_id: str) -> MigrationRecord:
    """Get migration record by ID."""
    record = _service.get_migration(migration_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Migration {migration_id} not found")
    return record


@assurance_router.get("/{migration_id}/assurance")
def get_assurance_report(migration_id: str) -> MigrationAssuranceReport:
    """Get the full assurance report for a migration."""
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
    events = _service.get_events(migration_id)
    return [e.model_dump() for e in events]
