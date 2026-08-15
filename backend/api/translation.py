"""FastAPI router for Phase 6 Translation Engine endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.translator.models import TranslationRequest, TranslationResult
from backend.translator.repository import get_translation_result
from backend.translator.service import TranslationService

translation_router = APIRouter(prefix="/api/v1/translations", tags=["Translation"])


@translation_router.post(
    "",
    response_model=TranslationResult,
    status_code=status.HTTP_201_CREATED,
    summary="Translate Source SQL to Candidate Target SQL",
)
def create_translation(
    request: TranslationRequest,
    mock_mode: str = Query("MOCK_GOOD", description="Mock scenario mode for testing"),
    db: Session = Depends(get_db),
) -> TranslationResult:
    """Submit a SQL translation request.

    Generates a candidate SQL migration payload using the Phase 6 translation engine.
    Does NOT execute or validate semantic equivalence.
    """
    return TranslationService.translate(request=request, db_session=db, mock_mode=mock_mode)


@translation_router.get(
    "/{translation_id}",
    response_model=TranslationResult,
    summary="Retrieve Translation Result Metadata",
)
def get_translation(
    translation_id: str,
    db: Session = Depends(get_db),
) -> TranslationResult:
    """Retrieve audit record for a given translation_id."""
    res = get_translation_result(translation_id, db_session=db)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Translation '{translation_id}' not found.",
        )
    return res
