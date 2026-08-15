"""Raw discrepancy signals extracted from Phase 4 validation results."""

from typing import Any

from pydantic import BaseModel, Field


class RawDiscrepancySignal(BaseModel):
    """Raw discrepancy signal extracted from validator execution artifacts."""

    source_validator: str
    signal_type: str
    analysis_path: str = ""
    source_expression: str | None = None
    target_expression: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
