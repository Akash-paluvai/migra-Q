from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from backend.diagnosis import CLASSIFIER_VERSION


class DiscrepancyCategory(str, Enum):
    """Mandatory primary discrepancy taxonomy."""

    BOUNDARY_CONDITION = "BOUNDARY_CONDITION"
    NULL_SEMANTICS = "NULL_SEMANTICS"
    JOIN_SEMANTICS = "JOIN_SEMANTICS"
    AGGREGATION_SEMANTICS = "AGGREGATION_SEMANTICS"
    DATE_SEMANTICS = "DATE_SEMANTICS"
    TYPE_CONVERSION = "TYPE_CONVERSION"
    FILTER_LOGIC = "FILTER_LOGIC"
    CASE_LOGIC = "CASE_LOGIC"
    COLUMN_MAPPING = "COLUMN_MAPPING"
    SET_SEMANTICS = "SET_SEMANTICS"
    UNKNOWN = "UNKNOWN"


class DiscrepancySeverity(str, Enum):
    """Evidence-driven deterministic severity levels."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ClassificationMethod(str, Enum):
    """Method used to classify discrepancy."""

    DETERMINISTIC_RULE = "DETERMINISTIC_RULE"
    STRUCTURAL_DIFF = "STRUCTURAL_DIFF"
    EXECUTION_EVIDENCE = "EXECUTION_EVIDENCE"
    COMBINED_DETERMINISTIC = "COMBINED_DETERMINISTIC"
    UNKNOWN = "UNKNOWN"


class TypedEvidenceType(str, Enum):
    """Typed evidence categories."""

    RULE_DIFF = "RULE_DIFF"
    JOIN_DIFF = "JOIN_DIFF"
    FILTER_DIFF = "FILTER_DIFF"
    AGGREGATE_DIFF = "AGGREGATE_DIFF"
    SCHEMA_DIFF = "SCHEMA_DIFF"
    ROW_DIFF = "ROW_DIFF"
    NULL_CASE = "NULL_CASE"
    BOUNDARY_CASE = "BOUNDARY_CASE"
    DATE_CASE = "DATE_CASE"
    TYPE_DIFF = "TYPE_DIFF"
    MISSING_ROW = "MISSING_ROW"
    EXTRA_ROW = "EXTRA_ROW"
    DUPLICATE_KEY = "DUPLICATE_KEY"
    AGGREGATE_RESULT_DIFF = "AGGREGATE_RESULT_DIFF"


class TypedEvidence(BaseModel):
    """Typed evidence item referencing actual deterministic facts."""

    type: str
    column: str | None = None
    value: Any = None
    source_result: Any = None
    target_result: Any = None
    row_key: dict[str, Any] | None = None
    detail: str = ""
    ordinal: int = 0


class ImpactMetrics(BaseModel):
    """Impact metrics computed for a classified discrepancy."""

    affected_row_count: int = 0
    total_output_rows: int = 0
    affected_percentage: float = 0.0
    affected_column_count: int = 0
    aggregate_delta: dict[str, Any] | None = None


class DiscrepancyRecord(BaseModel):
    """Structured record of a distinct semantic discrepancy."""

    discrepancy_id: str  # D-001, D-002 ...
    validation_id: str
    category: DiscrepancyCategory
    subcategory: str | None = None
    severity: DiscrepancySeverity
    classification_confidence: float = Field(..., ge=0.0, le=1.0)
    status: str = "OPEN"
    source_location: str = ""
    target_location: str = ""
    source_expression: str | None = None
    target_expression: str | None = None
    affected_output_columns: list[str] = Field(default_factory=list)
    affected_row_count: int = 0
    total_output_rows: int = 0
    affected_percentage: float = 0.0
    evidence: list[TypedEvidence] = Field(default_factory=list)
    validator_checks: list[str] = Field(default_factory=list)
    classification_method: ClassificationMethod
    classification_reason: str
    analysis_path: str = ""
    discrepancy_signature: str = ""
    created_at: str

class DiscrepancyReport(BaseModel):
    """Complete aggregated discrepancy report for a validation."""

    diagnosis_id: str
    validation_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    classifier_version: str = CLASSIFIER_VERSION
    discrepancies: list[DiscrepancyRecord] = Field(default_factory=list)
    discrepancy_count: int = 0
    category_counts: dict[str, int] = Field(default_factory=dict)
    severity_counts: dict[str, int] = Field(default_factory=dict)
    summary_statistics: dict[str, Any] = Field(default_factory=dict)
