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
    record = _service.get_migration("MIG-7BF1E8BDF850")
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


class CandidateEditRequest(BaseModel):
    edited_sql: str


@assurance_router.post("/{migration_id}/candidate")
def edit_candidate(migration_id: str, req: CandidateEditRequest) -> dict[str, Any]:
    """Submit a new edited SQL candidate and re-run preflight validation."""
    from backend.assurance.service import create_candidate_version, get_active_candidate, save_candidate
    from backend.preflight.validator import SchemaPreflightValidator
    
    if migration_id == "flagship":
        flg = _service.get_flagship_migration()
        migration_id = flg.migration_id

    record = _service.get_migration(migration_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Migration {migration_id} not found")

    current_candidate = get_active_candidate(migration_id)
    parent_id = current_candidate.candidate_id if current_candidate else None

    # Create new user-edited candidate
    new_candidate = create_candidate_version(
        migration_id=migration_id,
        sql_text=req.edited_sql,
        source="USER",
        parent_version_id=parent_id
    )

    # Run preflight
    preflight = SchemaPreflightValidator.validate(
        sql=req.edited_sql, 
        dataset_id=record.dataset_id, 
        dialect=record.target_dialect
    )
    
    new_candidate.preflight_summary = preflight
    new_candidate.preflight_status = preflight.status
    save_candidate(new_candidate)

    # Atomically restart pipeline state downstream and bind to new candidate
    _service.reset_downstream_pipeline_state(
        migration_id=migration_id, 
        candidate_id=new_candidate.candidate_id,
        preflight_summary=preflight
    )
    
    return {
        "candidate_id": new_candidate.candidate_id,
        "preflight_summary": preflight.model_dump()
    }


@assurance_router.post("/{migration_id}/source_candidate")
def edit_source_candidate(migration_id: str, req: CandidateEditRequest) -> dict[str, Any]:
    """Submit a new edited Source SQL candidate and re-run the pipeline from translation."""
    from backend.assurance.service import create_source_candidate_version
    
    if migration_id == "flagship":
        flg = _service.get_flagship_migration()
        migration_id = flg.migration_id

    record = _service.get_migration(migration_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Migration {migration_id} not found")

    # Create new user-edited source candidate
    new_candidate = create_source_candidate_version(
        migration_id=migration_id,
        sql_text=req.edited_sql,
        origin="USER",
        dialect=record.source_dialect
    )

    # Wipe downstream pipeline state (it will be regenerated by the orchestrator)
    _service.reset_downstream_pipeline_state(
        migration_id=migration_id, 
        candidate_id=None,
        preflight_summary=None
    )

    # Re-run pipeline from the start using the newly active source candidate
    from backend.orchestrator import PipelineRunRequest
    result = _orchestrator.run(
        PipelineRunRequest(
            migration_id=migration_id,
            source_sql=new_candidate.sql_text,
            source_dialect=record.source_dialect,
            target_dialect=record.target_dialect,
            dataset_id=record.dataset_id,
        )
    )
    
    # Return new orchestrator report summary
    return {
        "source_candidate_id": new_candidate.candidate_id,
        "migration_id": migration_id,
        "final_status": result.migration_record.final_status
    }


@assurance_router.get("/{migration_id}/source_candidate/active")
def get_active_source_candidate_api(migration_id: str) -> dict[str, Any]:
    """Get the active source candidate for a migration."""
    from backend.assurance.service import get_active_source_candidate
    
    if migration_id == "flagship":
        flg = _service.get_flagship_migration()
        migration_id = flg.migration_id
        
    candidate = get_active_source_candidate(migration_id)
    if not candidate:
        raise HTTPException(status_code=404, detail=f"No active source candidate found for {migration_id}")
        
    report = _service.get_assurance_report(migration_id)
    return {
        "candidate": candidate.model_dump(),
        "preflight_summary": candidate.preflight_summary.model_dump() if candidate.preflight_summary else None,
        "pipeline_status": report.final_status.value if report else None
    }


@assurance_router.get("/{migration_id}/candidate/active")
def get_active_candidate_api(migration_id: str) -> dict[str, Any]:
    """Get the active candidate for a migration."""
    from backend.assurance.service import get_active_candidate
    
    if migration_id == "flagship":
        flg = _service.get_flagship_migration()
        migration_id = flg.migration_id
        
    candidate = get_active_candidate(migration_id)
    if not candidate:
        raise HTTPException(status_code=404, detail=f"No active candidate found for {migration_id}")
        
    report = _service.get_assurance_report(migration_id)
    execution_status = "NOT_RUN"
    can_execute = False
    
    if report:
        if report.execution_summary:
            execution_status = "RUN"
            
    if candidate.preflight_status == "PASS" and execution_status == "NOT_RUN":
        can_execute = True
        
    return {
        "id": candidate.candidate_id,
        "version": candidate.version,
        "source": candidate.source,
        "sql": candidate.sql_text,
        "preflight_status": candidate.preflight_status,
        "execution_status": execution_status,
        "can_execute": can_execute
    }


@assurance_router.post("/{migration_id}/execute")
def execute_migration(migration_id: str) -> dict[str, Any]:
    """Execute Phase 3-9 for the active preflighted candidate."""
    if migration_id == "flagship":
        flg = _service.get_flagship_migration()
        migration_id = flg.migration_id

    try:
        result = _orchestrator.execute_migration(migration_id)
        return {
            "migration_id": result.migration_id,
            "final_status": result.migration_record.final_status
        }
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Execution error: {exc}")



@assurance_router.get("/{migration_id}")
def get_migration(migration_id: str) -> MigrationRecord:
    """Get migration record by ID."""
    if migration_id == "flagship":
        return get_flagship_migration()
    record = _service.get_migration(migration_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Migration {migration_id} not found")
        
    # Transparently load from artifact if needed
    if record.source_sql_storage == "artifact" and record.source_sql_ref:
        from pathlib import Path
        try:
            record.source_sql = Path(record.source_sql_ref).read_text(encoding="utf-8")
        except Exception as e:
            record.source_sql = f"-- Error loading source SQL from artifact: {e}"
            
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

