"""Pydantic models for structured SQL analysis output."""

from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel, Field

from backend.analyzer import ANALYZER_VERSION


class TableRef(BaseModel):
    name: str
    alias: str | None = None

    def __str__(self) -> str:
        return f"{self.name} AS {self.alias}" if self.alias else self.name


class ColumnRef(BaseModel):
    name: str
    table: str | None = None
    alias: str | None = None
    context: Literal[
        "select", "filter", "join", "group_by", "having", "order_by", "aggregate", "other"
    ] = "other"


class JoinInfo(BaseModel):
    id: str
    join_type: str  # INNER, LEFT, RIGHT, CROSS …
    left: str
    right: str
    condition: str


class FilterInfo(BaseModel):
    id: str
    scope: Literal["WHERE", "HAVING"]
    expression: str


class AggregationInfo(BaseModel):
    id: str
    function: str  # SUM, COUNT, AVG …
    expression: str
    distinct: bool = False
    group_by: list[str] = Field(default_factory=list)


class CaseWhen(BaseModel):
    condition: str
    result: str


class CaseExpression(BaseModel):
    id: str
    whens: list[CaseWhen]
    else_result: str | None = None
    target_column: str | None = None


class BusinessRule(BaseModel):
    id: str
    type: str  # comparison, range, null_check …
    condition: dict  # {operator, left, right} etc.
    then: str
    else_val: str | None = Field(None, alias="else")

    model_config = {"populate_by_name": True}


class NullSensitiveExpr(BaseModel):
    id: str
    expression: str
    kind: str  # IS_NULL, IS_NOT_NULL, COALESCE, NULLIF


class AnalysisWarning(BaseModel):
    code: str
    message: str
    location: str | None = None


class SQLAnalysis(BaseModel):
    """Top-level analysis result for a single SQL statement."""

    dialect: str
    original_sql: str
    normalized_sql: str
    sql_hash: str
    analyzer_version: str = ANALYZER_VERSION

    tables: list[TableRef] = Field(default_factory=list)
    columns: list[ColumnRef] = Field(default_factory=list)
    joins: list[JoinInfo] = Field(default_factory=list)
    filters: list[FilterInfo] = Field(default_factory=list)
    aggregations: list[AggregationInfo] = Field(default_factory=list)
    case_expressions: list[CaseExpression] = Field(default_factory=list)
    business_rules: list[BusinessRule] = Field(default_factory=list)
    null_sensitive_expressions: list[NullSensitiveExpr] = Field(default_factory=list)
    warnings: list[AnalysisWarning] = Field(default_factory=list)
    errors: list[AnalysisWarning] = Field(default_factory=list)

    @staticmethod
    def compute_hash(sql: str) -> str:
        return hashlib.sha256(sql.strip().encode()).hexdigest()[:16]
