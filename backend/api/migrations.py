from fastapi import APIRouter, HTTPException
from backend.core.models import MigrationRequest, Dialect
from backend.storage.repository import MigrationRepository
from backend.translator.schemas import TranslationTask
from backend.translator.translator import SQLTranslator

router = APIRouter()


@router.post("/")
def create_migration_job(request: MigrationRequest):
    """Submit a new SQL migration job for translation and parsing."""
    try:
        task = TranslationTask(
            source_sql=request.source_sql,
            source_dialect=request.source_dialect,
            target_dialect=request.target_dialect
        )

        translated = SQLTranslator.translate(task)
        target_sql = request.target_sql or translated.translated_sql

        job_data = {
            "source_dialect": request.source_dialect,
            "target_dialect": request.target_dialect,
            "source_sql": request.source_sql,
            "target_sql": target_sql,
            "status": "translated",
            "sample_data": request.sample_data_json or {
                "sample_table": [
                    {"id": 1, "amount": 100.0, "status": "active"},
                    {"id": 2, "amount": 250.0, "status": "pending"}
                ]
            }
        }
        migration_id = MigrationRepository.save_migration(job_data)
        return {
            "migration_id": migration_id,
            "status": "translated",
            "target_sql": target_sql,
            "used_llm_fallback": translated.used_llm_fallback
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{migration_id}")
def get_migration_status(migration_id: str):
    """Get migration job details by ID."""
    job = MigrationRepository.get_migration(migration_id)
    if not job:
        raise HTTPException(status_code=404, detail="Migration job not found")
    return job
