"""FastAPI endpoints for Phase 5 discrepancy diagnosis."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.diagnosis.models import DiscrepancyReport
from backend.diagnosis.service import DiagnosisService

diagnosis_router = APIRouter(prefix="/api/v1/diagnoses", tags=["diagnosis"])


class DiagnosisCreateRequest(BaseModel):
    validation_id: str
    max_evidence_items: int = 100


@diagnosis_router.post("", response_model=DiscrepancyReport, status_code=status.HTTP_201_CREATED)
def create_diagnosis(request: DiagnosisCreateRequest) -> DiscrepancyReport:
    """Run discrepancy classification and evidence consolidation on a ValidationReport."""
    try:
        return DiagnosisService.diagnose_validation(
            validation_id=request.validation_id,
            max_evidence_items=request.max_evidence_items,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Diagnosis failed: {exc}",
        ) from exc


@diagnosis_router.get("/{diagnosis_id}", response_model=DiscrepancyReport)
def get_diagnosis(diagnosis_id: str) -> DiscrepancyReport:
    """Retrieve a stored DiscrepancyReport by diagnosis_id."""
    report = DiagnosisService.get_diagnosis(diagnosis_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnosis ID '{diagnosis_id}' not found.",
        )
    return report
