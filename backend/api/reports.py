from fastapi import APIRouter, HTTPException
from backend.assurance.report import AssuranceReportGenerator
from backend.assurance.scoring import AssuranceScorer
from backend.core.models import ValidationPipelineResult
from backend.storage.repository import MigrationRepository

router = APIRouter()


@router.get("/{migration_id}/scorecard")
def get_scorecard(migration_id: str):
    """Retrieve assurance scorecard for migration."""
    job = MigrationRepository.get_migration(migration_id)
    if not job or "validation_result" not in job:
        raise HTTPException(status_code=404, detail="Validation result not found for migration ID")

    val_result = ValidationPipelineResult(**job["validation_result"])
    scorecard = AssuranceScorer.calculate_score(val_result)
    return scorecard


@router.get("/{migration_id}/markdown")
def get_markdown_report(migration_id: str):
    """Generate Markdown summary report."""
    job = MigrationRepository.get_migration(migration_id)
    if not job or "validation_result" not in job:
        raise HTTPException(status_code=404, detail="Validation result not found for migration ID")

    val_result = ValidationPipelineResult(**job["validation_result"])
    scorecard = AssuranceScorer.calculate_score(val_result)
    markdown_content = AssuranceReportGenerator.generate_markdown_report(val_result, scorecard)

    return {"report_markdown": markdown_content}
