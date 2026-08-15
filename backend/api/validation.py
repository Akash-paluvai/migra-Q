"""FastAPI routes for semantic validation endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.validation.models import ValidationConfig, ValidationReport
from backend.validation.service import ValidationService

validation_router = APIRouter(prefix="/api/v1/validations", tags=["validations"])


class CreateValidationRequest(BaseModel):
    """Payload for triggering a semantic validation run."""

    source_execution_id: str
    target_execution_id: str
    source_analysis: dict[str, Any] | None = None
    target_analysis: dict[str, Any] | None = None
    config: ValidationConfig | None = None
    benchmark_scenario: dict[str, Any] | None = None


@validation_router.post("", response_model=ValidationReport)
def create_validation(payload: CreateValidationRequest) -> ValidationReport:
    """Execute semantic validation between two Phase 3 execution artifacts."""
    try:
        report = ValidationService.validate_executions(
            source_execution_id=payload.source_execution_id,
            target_execution_id=payload.target_execution_id,
            source_analysis=payload.source_analysis,
            target_analysis=payload.target_analysis,
            config=payload.config,
            benchmark_scenario=payload.benchmark_scenario,
        )
        return report
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@validation_router.get("/{validation_id}", response_model=ValidationReport)
def get_validation(validation_id: str) -> ValidationReport:
    """Retrieve a completed ValidationReport by validation_id."""
    report = ValidationService.get_validation(validation_id)
    if not report:
        raise HTTPException(
            status_code=404, detail=f"Validation report '{validation_id}' not found."
        )
    return report
