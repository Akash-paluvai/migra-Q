"""ValidationContext container providing read-only inputs for validators."""

from typing import Any

from pydantic import BaseModel, Field

from backend.analyzer.models import SQLAnalysis
from backend.execution.models import ExecutionResult
from backend.validation.models import ValidationConfig


class ValidationContext(BaseModel):
    """Read-only validation context holding execution results and SQL analysis."""

    source_execution: ExecutionResult
    target_execution: ExecutionResult
    source_analysis: SQLAnalysis | None = None
    target_analysis: SQLAnalysis | None = None
    dataset_manifest: dict[str, Any] | None = None
    config: ValidationConfig = Field(default_factory=ValidationConfig)
    benchmark_scenario: dict[str, Any] | None = None
