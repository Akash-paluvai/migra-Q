"""FastAPI API endpoints for Phase 8 Repair Execution & Deterministic Re-Validation Engine."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.repair_verification.models import RepairOutcome, RepairVerificationResult
from backend.repair_verification.repository import get_outcomes_by_verification_id
from backend.repair_verification.service import RepairVerificationService

repair_verification_router = APIRouter(prefix="/api/v1/repair-verifications", tags=["repair-verification"])


class CreateVerificationRequest(BaseModel):
    """Request payload for triggering repair verification."""

    repair_id: str
    discrepancy_id: str | None = None
    target_dialect: str = "bigquery"


@repair_verification_router.post(
    "",
    response_model=RepairVerificationResult,
    summary="Trigger deterministic repair execution and re-validation",
)
def create_repair_verification(req: CreateVerificationRequest) -> RepairVerificationResult:
    """Execute candidate repair, re-validate via Phase 4/5, and return verification result."""
    try:
        return RepairVerificationService.verify_repair(
            repair_id=req.repair_id,
            discrepancy_id=req.discrepancy_id,
            target_dialect=req.target_dialect,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Repair verification failed: {exc}")


@repair_verification_router.get(
    "/{verification_id}",
    response_model=RepairVerificationResult,
    summary="Retrieve repair verification result by ID",
)
def get_repair_verification_by_id(verification_id: str) -> RepairVerificationResult:
    """Retrieve RepairVerificationResult artifact by verification_id."""
    res = RepairVerificationService.get_verification(verification_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Repair verification '{verification_id}' not found.")
    return res


@repair_verification_router.get(
    "/{verification_id}/outcomes",
    response_model=list[RepairOutcome],
    summary="Retrieve repair outcomes for verification ID",
)
def get_repair_outcomes(verification_id: str) -> list[RepairOutcome]:
    """Retrieve list of RepairOutcomes for verification_id."""
    outcomes = get_outcomes_by_verification_id(verification_id)
    if not outcomes:
        res = RepairVerificationService.get_verification(verification_id)
        if not res:
            raise HTTPException(status_code=404, detail=f"Repair verification '{verification_id}' not found.")
        outcomes = res.outcomes
    return outcomes
