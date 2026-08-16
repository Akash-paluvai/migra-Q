"""Domain models, contracts, and schema definitions for Phase 6 Translation Engine."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ColumnSchemaDef(BaseModel):
    """Definition of a database column in target schema context."""

    name: str
    type: str


class TableSchema(BaseModel):
    """Definition of a table schema in target schema context."""

    name: str
    columns: list[ColumnSchemaDef] = Field(default_factory=list)


class SchemaContext(BaseModel):
    """Explicit schema context provided with translation requests."""

    tables: list[TableSchema] = Field(default_factory=list)

    def get_table_names(self) -> set[str]:
        """Return set of table names in schema context."""
        return {t.name.lower() for t in self.tables}

    def get_column_names(self, table_name: str | None = None) -> set[str]:
        """Return set of column names, optionally filtered by table."""
        cols = set()
        for t in self.tables:
            if table_name is None or t.name.lower() == table_name.lower():
                for c in t.columns:
                    cols.add(c.name.lower())
        return cols


class StructuredRule(BaseModel):
    """Representation of a migrated structural rule."""

    source_path: str
    source_expression: str
    target_expression: str
    rule_type: str = "comparison"


class TranslationRequest(BaseModel):
    """Input payload for a SQL translation request."""

    source_sql: str
    source_dialect: str = "teradata"
    target_dialect: str = "bigquery"
    dataset_id: str | None = None
    migration_id: str | None = None
    schema_context: SchemaContext | None = Field(default=None, alias="schema")
    analysis_reference: str | None = None
    request_id: str | None = None

    model_config = {"populate_by_name": True}


class TranslationContext(BaseModel):
    """Normalized structured context passed to prompt engineering."""

    source_sql: str
    normalized_sql: str
    source_dialect: str
    target_dialect: str
    tables: list[dict[str, Any]] = Field(default_factory=list)
    columns: list[dict[str, Any]] = Field(default_factory=list)
    joins: list[dict[str, Any]] = Field(default_factory=list)
    filters: list[dict[str, Any]] = Field(default_factory=list)
    aggregations: list[dict[str, Any]] = Field(default_factory=list)
    business_rules: list[dict[str, Any]] = Field(default_factory=list)
    case_expressions: list[dict[str, Any]] = Field(default_factory=list)
    null_sensitive_expressions: list[dict[str, Any]] = Field(default_factory=list)
    schema_context: SchemaContext | None = Field(default=None, alias="schema")
    context_hash: str = ""

    model_config = {"populate_by_name": True}


class TranslationResponse(BaseModel):
    """Structured LLM output response model."""

    target_sql: str
    assumptions: list[str] = Field(default_factory=list)
    potential_risks: list[str] = Field(default_factory=list)
    translated_rules: list[StructuredRule] = Field(default_factory=list)


class CandidateValidationStatus(str, Enum):
    """Candidate target SQL syntactic & safety validation status."""

    VALID_SYNTAX = "VALID_SYNTAX"
    INVALID_SYNTAX = "INVALID_SYNTAX"
    UNSAFE_SQL = "UNSAFE_SQL"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    NOT_EVALUATED = "NOT_EVALUATED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TranslationStatus(str, Enum):
    """Overall translation operation status."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    UNSUPPORTED_DIALECT = "UNSUPPORTED_DIALECT"
    TIMEOUT = "TIMEOUT"
    PROVIDER_ERROR = "PROVIDER_ERROR"


class TranslationMetadata(BaseModel):
    """Metadata audit attributes captured for every translation attempt."""

    translation_id: str
    request_id: str
    migration_id: str | None = None
    provider: str
    model: str
    source_dialect: str
    target_dialect: str
    source_sql_hash: str
    translation_context_hash: str
    prompt_hash: str
    created_at: str
    duration_ms: float = 0.0
    retry_count: int = 0
    input_token_count: int | None = None
    output_token_count: int | None = None
    total_token_count: int | None = None
    estimated_cost: float | None = None
    error_code: str | None = None
    error_message: str | None = None
    translator_version: str = "0.1.0"
    prompt_version: str = "0.1.0"


class TranslationResult(BaseModel):
    """Top-level Phase 6 translation result artifact."""

    metadata: TranslationMetadata
    status: TranslationStatus
    candidate_validation_status: CandidateValidationStatus | None = None
    semantic_status: str = "NOT_EVALUATED"
    response: TranslationResponse | None = None
    validation_summary: str = ""
    structural_differences: list[str] = Field(default_factory=list)

    @classmethod
    def model_validate(cls, *args, **kwargs):
        res = super().model_validate(*args, **kwargs)
        if res.status != TranslationStatus.SUCCESS and res.candidate_validation_status == CandidateValidationStatus.VALID_SYNTAX:
            raise ValueError(
                f"IMPOSSIBLE_STATE: Translation status '{res.status}' cannot have candidate_validation_status 'VALID_SYNTAX'."
            )
        return res

