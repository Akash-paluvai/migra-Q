"""POST /api/v1/analyze — SQL analysis endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.analyzer.service import analyze
from backend.core.exceptions import ParserError

router = APIRouter()


class AnalyzeRequest(BaseModel):
    sql: str
    dialect: str = "teradata"


@router.post("/api/v1/analyze")
def analyze_sql(req: AnalyzeRequest) -> dict:
    """Analyze a SQL statement and return structured extraction."""
    try:
        result = analyze(req.sql, dialect=req.dialect)
        return result.model_dump()
    except ParserError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
