"""Phase 9 & 10 Migration Assurance & Management API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.assurance.models import MigrationAssuranceReport, MigrationRecord
from backend.assurance.service import MigrationAssuranceService
from backend.orchestrator import MigrationOrchestrator
from backend.orchestrator.models import MigrationRunResponse

assurance_router = APIRouter(prefix="/api/v1/migrations", tags=["assurance"])

_service = MigrationAssuranceService()
_orchestrator = MigrationOrchestrator()


class MigrationRunRequest(BaseModel):
    source_sql: str
    source_dialect: str
    target_dialect: str
    dataset_id: str
    mock_mode: str | None = None


@assurance_router.get("")
def list_migrations() -> list[MigrationRecord]:
    """Get all migration records."""
    return _service.list_migrations()


@assurance_router.get("/flagship")
def get_flagship_migration() -> MigrationRecord:
    """Retrieve flagship migration record if it exists (retrieval only, no auto-create)."""
    record = _service.get_migration("MIG-FLAGSHIP-001")
    if record is None:
        raise HTTPException(status_code=404, detail="Flagship migration not found. Run the flagship demo script to create it.")
    return record


@assurance_router.post("/preflight")
def preflight_check(req: MigrationRunRequest) -> dict[str, Any]:
    """Preflight validation check verifying SQL syntax and dataset table compatibility."""
    try:
        return _orchestrator.preflight_check(req.source_sql, req.dataset_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Preflight error: {exc}")


@assurance_router.post("/run", response_model=MigrationRunResponse)
def run_migration(req: MigrationRunRequest) -> MigrationRunResponse:
    """Trigger a new migration workflow run dynamically via MigrationOrchestrator."""
    try:
        from backend.orchestrator import PipelineRunRequest
        result = _orchestrator.run(
            PipelineRunRequest(
                source_sql=req.source_sql,
                source_dialect=req.source_dialect,
                target_dialect=req.target_dialect,
                dataset_id=req.dataset_id,
                mock_mode=req.mock_mode,
            )
        )
        rec = result.migration_record
        return MigrationRunResponse(
            migration_id=rec.migration_id,
            current_state=rec.current_state,
            source_dialect=rec.source_dialect,
            target_dialect=rec.target_dialect,
            dataset_id=rec.dataset_id,
            source_sql_hash=rec.source_sql_hash,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline execution error: {exc}")


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


@assurance_router.get("/{migration_id}/discrepancies")
def get_discrepancies(migration_id: str) -> dict[str, Any]:
    """Get canonical Phase 5 discrepancy data for a migration.

    Retrieves the full DiscrepancyReport via the audit lineage diagnosis_id,
    NOT from the Phase 9 assurance summary. This provides the canonical
    source-of-truth for discrepancy details, expressions, and evidence.
    """
    report = _service.get_assurance_report(migration_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail=f"Assurance report for migration {migration_id} not found",
        )

    diagnosis_id = report.lineage.diagnosis_id
    if not diagnosis_id:
        return {
            "migration_id": migration_id,
            "diagnosis_id": None,
            "discrepancy_count": 0,
            "discrepancies": [],
            "status": "NO_DISCREPANCIES",
        }

    from backend.diagnosis.service import DiagnosisService

    disc_report = DiagnosisService.get_diagnosis(diagnosis_id)
    if disc_report is None:
        return {
            "migration_id": migration_id,
            "diagnosis_id": diagnosis_id,
            "discrepancy_count": 0,
            "discrepancies": [],
            "status": "DIAGNOSIS_NOT_FOUND",
        }

    return {
        "migration_id": migration_id,
        "diagnosis_id": disc_report.diagnosis_id,
        "validation_id": disc_report.validation_id,
        "discrepancy_count": disc_report.discrepancy_count,
        "discrepancies": [d.model_dump() for d in disc_report.discrepancies],
        "category_counts": disc_report.category_counts,
        "severity_counts": disc_report.severity_counts,
        "status": "RESOLVED" if disc_report.discrepancy_count == 0 else "DISCREPANCIES_FOUND",
    }

