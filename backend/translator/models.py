"""Domain models, contracts, and schema definitions for Phase 6 Translation Engine."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field


class NormalizedTransformation(BaseModel):
    """Normalized, deduplicated translation transformation for UI/API consumption."""

    type: Literal["STRUCTURAL_DIFFERENCE", "TRANSLATED_RULE", "ASSUMPTION"]
    source: str
    target: str
    occurrences: int = 1
    explanation: str = ""


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
    dataset_id: str | None = None
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

    @computed_field
    @property
    def transformations(self) -> list[NormalizedTransformation]:
        """Dynamically compute normalized transformations from translation metadata."""
        if self.status != TranslationStatus.SUCCESS:
            return []

        evidence_map: dict[tuple[str, str], NormalizedTransformation] = {}

        def add_transformation(t_type: Literal["STRUCTURAL_DIFFERENCE", "TRANSLATED_RULE", "ASSUMPTION"], source: str, target: str, explanation: str):
            # Normalize whitespace/case for deduplication grouping
            norm_source = source.strip()
            norm_target = target.strip()
            # We don't include t_type in the key so we can deduplicate the exact same mapping 
            # if it appears in both structural_differences and translated_rules.
            key = (norm_source, norm_target)
            
            if key in evidence_map:
                # If we see it again from the same source, it's another occurrence.
                # If it's from a different source (e.g. structural diff vs translated rule),
                # we don't necessarily want to double count the occurrence of the logical rule.
                # But for simplicity, we'll increment if it's the exact same type, otherwise just keep it as 1?
                # Actually, user said: "If both sources describe the same actual transformation, deduplicate it... I recommend not counting the same evidence twice."
                # We can store sources seen.
                existing = evidence_map[key]
                # If we've already seen this exact type, it's a true multiple occurrence
                if existing.type == t_type:
                    existing.occurrences += 1
            else:
                evidence_map[key] = NormalizedTransformation(
                    type=t_type,
                    source=source,
                    target=target,
                    occurrences=1,
                    explanation=explanation
                )

        if self.response and self.response.translated_rules:
            for rule in self.response.translated_rules:
                # Deduplicate identical translated rules
                # e.g., NVL -> COALESCE
                add_transformation(
                    t_type="TRANSLATED_RULE",
                    source=rule.source_expression,
                    target=rule.target_expression,
                    explanation=f"Translated {rule.rule_type} rule"
                )

        if self.structural_differences:
            for diff in self.structural_differences:
                # Format is usually just a string describing the diff.
                # If it contains '->', try to parse it to match translated rules
                if "->" in diff:
                    parts = diff.split("->", 1)
                    add_transformation(
                        t_type="STRUCTURAL_DIFFERENCE",
                        source=parts[0].strip(),
                        target=parts[1].strip(),
                        explanation=diff
                    )
                else:
                    add_transformation(
                        t_type="STRUCTURAL_DIFFERENCE",
                        source="STRUCTURAL_DIFFERENCE",
                        target=diff,
                        explanation=diff
                    )
                
        if self.response and self.response.assumptions:
            for assumption in self.response.assumptions:
                add_transformation(
                    t_type="ASSUMPTION",
                    source="ASSUMPTION",
                    target=assumption,
                    explanation=assumption
                )

        return list(evidence_map.values())

    @computed_field
    @property
    def transformation_count(self) -> int:
        """Return the number of actual transformations (excluding assumptions)."""
        return len([t for t in self.transformations if t.type != "ASSUMPTION"])

    @computed_field
    @property
    def assumption_count(self) -> int:
        """Return the number of assumptions."""
        return len([t for t in self.transformations if t.type == "ASSUMPTION"])

    @classmethod
    def model_validate(cls, *args, **kwargs):
        res = super().model_validate(*args, **kwargs)
        if res.status != TranslationStatus.SUCCESS and res.candidate_validation_status == CandidateValidationStatus.VALID_SYNTAX:
            raise ValueError(
                f"IMPOSSIBLE_STATE: Translation status '{res.status}' cannot have candidate_validation_status 'VALID_SYNTAX'."
            )
        return res

