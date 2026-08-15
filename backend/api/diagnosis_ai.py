"""FastAPI router for Phase 7 AI Diagnosis & Repair Proposal Engine."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.db.database import get_db_session
from backend.db.models import RepairChangeRecordModel, RepairProposalRecord
from backend.diagnosis_ai.models import (
    DiagnosisAIResult,
    GroundedClaim,
    RepairChange,
    RepairProposal,
    RepairStatus,
)
from backend.diagnosis_ai.repository import get_diagnosis_ai_result
from backend.diagnosis_ai.service import DiagnosisAIService

diagnosis_ai_router = APIRouter(prefix="/api/v1", tags=["diagnosis-ai"])


class AIDiagnosisRequest(BaseModel):
    """Request payload for triggering Phase 7 AI Diagnosis."""

    discrepancy_id: str = "D-001"
    category: str = "BOUNDARY_CONDITION"
    severity: str = "HIGH"
    source_sql: str = Field(..., description="Source SQL string")
    target_sql: str = Field(..., description="Target candidate SQL string")
    source_dialect: str = "teradata"
    target_dialect: str = "bigquery"
    source_expression: str | None = "t.amount > 500"
    target_expression: str | None = "t.amount >= 500"
    analysis_path: str | None = "columns[risk_class]"
    affected_row_count: int = 10512
    affected_percentage: float = 10.51
    affected_columns: list[str] = Field(default_factory=lambda: ["risk_class"])
    representative_examples: list[dict[str, Any]] = Field(default_factory=list)
    structural_differences: list[str] = Field(default_factory=list)
    mock_mode: str | None = None


@diagnosis_ai_router.post("/ai-diagnoses", response_model=DiagnosisAIResult)
def create_ai_diagnosis(req: AIDiagnosisRequest) -> DiagnosisAIResult:
    """Run AI diagnosis and generate candidate repair proposal."""
    try:
        return DiagnosisAIService.diagnose_discrepancy(
            discrepancy_id=req.discrepancy_id,
            category=req.category,
            severity=req.severity,
            source_sql=req.source_sql,
            target_sql=req.target_sql,
            source_dialect=req.source_dialect,
            target_dialect=req.target_dialect,
            source_expression=req.source_expression,
            target_expression=req.target_expression,
            analysis_path=req.analysis_path,
            affected_row_count=req.affected_row_count,
            affected_percentage=req.affected_percentage,
            affected_columns=req.affected_columns,
            representative_examples=req.representative_examples,
            structural_differences=req.structural_differences,
            mock_mode=req.mock_mode,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@diagnosis_ai_router.get("/ai-diagnoses/{diagnosis_id}", response_model=DiagnosisAIResult)
def get_ai_diagnosis(diagnosis_id: str) -> DiagnosisAIResult:
    """Retrieve existing AI diagnosis result by diagnosis_id."""
    res = get_diagnosis_ai_result(diagnosis_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"AI Diagnosis '{diagnosis_id}' not found.")
    return res


@diagnosis_ai_router.get("/repair-proposals/{repair_id}", response_model=RepairProposal)
def get_repair_proposal_by_id(repair_id: str) -> RepairProposal:
    """Retrieve existing candidate repair proposal by repair_id."""
    from backend.diagnosis_ai.repository import _IN_MEMORY_REPAIR_STORE

    try:
        session = get_db_session()
    except Exception:
        mem_rep = _IN_MEMORY_REPAIR_STORE.get(repair_id)
        if mem_rep:
            return mem_rep
        raise HTTPException(status_code=404, detail=f"Repair proposal '{repair_id}' not found.")

    try:
        rep_rec = session.query(RepairProposalRecord).filter_by(repair_id=repair_id).first()
        if not rep_rec:
            mem_rep = _IN_MEMORY_REPAIR_STORE.get(repair_id)
            if mem_rep:
                return mem_rep
            raise HTTPException(status_code=404, detail=f"Repair proposal '{repair_id}' not found.")

        chg_recs = session.query(RepairChangeRecordModel).filter_by(repair_id=repair_id).all()
        changes = [
            RepairChange(
                location=chg.location,
                before_expression=chg.before_expression,
                after_expression=chg.after_expression,
                change_type=chg.change_type,
            )
            for chg in chg_recs
        ]

        import json

        rep_claims = [GroundedClaim(**c) for c in (json.loads(rep_rec.claims_json) if rep_rec.claims_json else [])]
        rep_constraints = json.loads(rep_rec.constraints_checked_json) if rep_rec.constraints_checked_json else []

        return RepairProposal(
            repair_id=rep_rec.repair_id,
            discrepancy_id=rep_rec.discrepancy_id,
            status=RepairStatus(rep_rec.status),
            original_sql=rep_rec.original_sql or "",
            proposed_sql=rep_rec.proposed_sql or "",
            changed_region=rep_rec.changed_region or "",
            changes=changes,
            rationale=rep_rec.rationale or "",
            expected_effect=rep_rec.expected_effect or "",
            claims=rep_claims,
            constraints_checked=rep_constraints,
            repair_confidence=rep_rec.repair_confidence,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()
