from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Dialect(str, Enum):
    ORACLE = "oracle"
    POSTGRES = "postgres"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    DUCKDB = "duckdb"


class MigrationStatus(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    TRANSLATING = "translating"
    VALIDATING = "validating"
    DIAGNOSING = "diagnosing"
    REPAIRING = "repairing"
    PASSED = "passed"
    FAILED = "failed"


class MigrationRequest(BaseModel):
    source_dialect: Dialect
    target_dialect: Dialect
    source_sql: str
    target_sql: Optional[str] = None
    schema_ddl: Optional[str] = None
    sample_data_json: Optional[Dict[str, List[Dict[str, Any]]]] = None


class ASTDiffResult(BaseModel):
    source_ast_summary: str
    target_ast_summary: str
    structural_changes: List[str] = Field(default_factory=list)
    complexity_delta: float = 0.0


class SchemaValidationResult(BaseModel):
    passed: bool
    source_columns: List[str]
    target_columns: List[str]
    missing_columns: List[str] = Field(default_factory=list)
    type_mismatches: List[Dict[str, str]] = Field(default_factory=list)


class RowValidationResult(BaseModel):
    passed: bool
    source_row_count: int
    target_row_count: int
    matched_row_count: int
    mismatched_row_count: int
    sample_mismatches: List[Dict[str, Any]] = Field(default_factory=list)


class AggregateValidationResult(BaseModel):
    passed: bool
    metrics_compared: List[str] = Field(default_factory=list)
    diffs: Dict[str, float] = Field(default_factory=dict)


class BusinessRuleResult(BaseModel):
    rule_name: str
    passed: bool
    description: str
    observed_diff: Optional[str] = None


class EdgeCaseValidationResult(BaseModel):
    null_handling_passed: bool
    timezone_passed: bool
    floating_point_passed: bool
    collation_passed: bool
    details: List[str] = Field(default_factory=list)


class ValidationPipelineResult(BaseModel):
    migration_id: str
    passed: bool
    schema_check: SchemaValidationResult
    row_check: RowValidationResult
    aggregate_check: AggregateValidationResult
    business_rules_check: List[BusinessRuleResult] = Field(default_factory=list)
    edge_cases_check: EdgeCaseValidationResult
    overall_confidence_score: float = 0.0


class MismatchClassification(BaseModel):
    mismatch_type: str
    severity: str  # HIGH, MEDIUM, LOW
    description: str
    affected_nodes: List[str] = Field(default_factory=list)
    root_cause_explanation: str


class RepairPatch(BaseModel):
    patch_id: str
    original_target_sql: str
    repaired_target_sql: str
    diff_explanation: str
    confidence: float


class AssuranceScorecard(BaseModel):
    migration_id: str
    assurance_score: float  # 0 to 100
    gate_passed: bool
    score_breakdown: Dict[str, float]
    recommendations: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
