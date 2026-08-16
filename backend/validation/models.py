"""Validation domain models, contracts, and configuration schemas."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

VALIDATOR_VERSION = "0.1.0"


class ValidationCheckStatus(str, Enum):
    """Individual validator check status."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


class ValidationSeverity(str, Enum):
    """Check failure severity."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceType(str, Enum):
    """Categorized evidence types."""

    ROW_MISMATCH = "ROW_MISMATCH"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    MISSING_SOURCE_ROW = "MISSING_SOURCE_ROW"
    MISSING_TARGET_ROW = "MISSING_TARGET_ROW"
    VALUE_MISMATCH = "VALUE_MISMATCH"
    AGGREGATE_MISMATCH = "AGGREGATE_MISMATCH"
    RULE_MISMATCH = "RULE_MISMATCH"
    EDGE_CASE_FAILURE = "EDGE_CASE_FAILURE"
    DUPLICATE_KEY_WARNING = "DUPLICATE_KEY_WARNING"


class EvidenceItem(BaseModel):
    """Structured evidence detail for validation findings."""

    type: EvidenceType
    key: dict[str, Any] | None = None
    column: str | None = None
    source_value: Any = None
    target_value: Any = None
    category: str | None = None
    detail: str = ""


class ValidationResult(BaseModel):
    """Contract returned by every validator check."""

    check_name: str
    validator_version: str = VALIDATOR_VERSION
    status: ValidationCheckStatus
    severity: ValidationSeverity = ValidationSeverity.HIGH
    score: float = Field(..., ge=0.0, le=1.0)
    summary: str
    expected: Any = None
    actual: Any = None
    mismatch_count: int = 0
    evidence: list[EvidenceItem] = Field(default_factory=list)
    evidence_truncated: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0


class ValidationReport(BaseModel):
    """Complete aggregated validation report for a source-target comparison."""

    validation_id: str
    migration_id: str | None = None
    source_execution_id: str
    target_execution_id: str
    dataset_id: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    validator_version: str = VALIDATOR_VERSION
    checks: list[ValidationResult] = Field(default_factory=list)
    overall_status: str = "FAIL"  # PASS, WARN, FAIL, ERROR
    summary: dict[str, int] = Field(default_factory=dict)


class ValidationConfig(BaseModel):
    """Configurable tolerances, comparison keys, and validator settings."""

    comparison_key: list[str] = Field(default_factory=list)
    numeric_absolute_tolerance: float = 1e-6
    numeric_relative_tolerance: float = 1e-5
    schema_column_order_matters: bool = True
    max_evidence_items: int = 100
    aggregate_specs: list[dict[str, Any]] | None = None
    enabled_validators: list[str] | None = None
