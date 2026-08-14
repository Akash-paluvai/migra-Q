from fastapi import APIRouter, HTTPException
from backend.core.models import ValidationPipelineResult
from backend.diagnosis.classifier import MismatchClassifier
from backend.repair.repair_agent import RepairAgent
from backend.storage.repository import MigrationRepository

router = APIRouter()


@router.post("/{migration_id}/repair")
def trigger_repair(migration_id: str):
    """Trigger automated SQL repair agent for a failed migration query."""
    job = MigrationRepository.get_migration(migration_id)
    if not job:
        raise HTTPException(status_code=404, detail="Migration job not found")

    val_data = job.get("validation_result")
    if not val_data:
        raise HTTPException(status_code=400, detail="Run validation prior to repair trigger.")

    val_result = ValidationPipelineResult(**val_data)
    classifications = MismatchClassifier.classify(val_result)

    patch = RepairAgent.generate_patch(
        source_sql=job["source_sql"],
        target_sql=job["target_sql"],
        classifications=classifications
    )

    job["target_sql"] = patch.repaired_target_sql
    job["status"] = "repaired"
    job["repair_patch"] = patch.model_dump()
    MigrationRepository.save_migration(job)

    return patch
