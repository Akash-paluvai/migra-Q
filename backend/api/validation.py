from fastapi import APIRouter, HTTPException
from backend.execution.sandbox import ExecutionSandbox
from backend.storage.repository import MigrationRepository
from backend.validation.orchestrator import ValidationOrchestrator

router = APIRouter()


@router.post("/{migration_id}/run")
def run_validation(migration_id: str):
    """Trigger 5-stage validation pipeline for a migration job."""
    job = MigrationRepository.get_migration(migration_id)
    if not job:
        raise HTTPException(status_code=404, detail="Migration job not found")

    try:
        source_df, target_df = ExecutionSandbox.run_comparison(
            source_sql=job["source_sql"],
            target_sql=job["target_sql"],
            sample_tables=job.get("sample_data", {})
        )

        result = ValidationOrchestrator.run_pipeline(
            source_df=source_df,
            target_df=target_df,
            migration_id=migration_id
        )

        job["validation_result"] = result.model_dump()
        job["status"] = "passed" if result.passed else "failed"
        MigrationRepository.save_migration(job)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation execution failed: {str(e)}")
