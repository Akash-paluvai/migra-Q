"""Candidate SQL validator module for Phase 6 Translation Engine.

Validates candidate target SQL for parseability, read-only safety, and schema consistency.
Does NOT judge semantic equivalence or correctness.
"""

from __future__ import annotations

import re
from typing import Any

import sqlglot
from sqlglot import exp

from backend.translator.models import CandidateValidationStatus, SchemaContext

PROHIBITED_MUTATION_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "COPY",
    "ATTACH",
    "LOAD",
    "INSTALL",
}


def validate_candidate_sql(
    target_sql: str,
    target_dialect: str = "bigquery",
    schema_context: SchemaContext | None = None,
    source_tables: list[dict[str, Any]] | None = None,
    source_columns: list[dict[str, Any]] | None = None,
) -> tuple[CandidateValidationStatus, str, str]:
    """Validate target SQL candidate for syntax, read-only safety, and schema consistency.

    Returns (CandidateValidationStatus, error_code, summary_message).
    """
    cleaned_sql = target_sql.strip()

    if not cleaned_sql:
        return (
            CandidateValidationStatus.INVALID_SYNTAX,
            "EMPTY_SQL",
            "Candidate SQL is empty.",
        )

    # 1. Read-only safety check using keyword scanning & SQLGlot AST inspection
    # Check top-level statement keywords
    upper_sql = cleaned_sql.upper()
    tokens = re.findall(r"\b[A-Z_]+\b", upper_sql)
    for kw in PROHIBITED_MUTATION_KEYWORDS:
        if kw in tokens and kw != "SELECT":
            return (
                CandidateValidationStatus.UNSAFE_SQL,
                "TARGET_SQL_NOT_READ_ONLY",
                f"Candidate SQL contains prohibited mutating operation: '{kw}'.",
            )

    # 2. Parse check using SQLGlot
    try:
        # SQLGlot dialect mapping
        glot_dialect = target_dialect.lower()
        if glot_dialect == "teradata":
            glot_dialect = "teradata"
        elif glot_dialect in ("bigquery", "bq"):
            glot_dialect = "bigquery"

        parsed = sqlglot.parse_one(cleaned_sql, read=glot_dialect)
    except Exception as e:
        return (
            CandidateValidationStatus.INVALID_SYNTAX,
            "UNPARSEABLE_SQL",
            f"Candidate SQL could not be parsed for dialect '{target_dialect}': {e}",
        )

    # Confirm statement type is SELECT or Expression
    if not isinstance(parsed, (exp.Select, exp.Union, exp.Subquery, exp.Expression)):
        return (
            CandidateValidationStatus.UNSAFE_SQL,
            "TARGET_SQL_NOT_READ_ONLY",
            f"Candidate SQL root statement type '{type(parsed).__name__}' is not read-only.",
        )

    # 3. Target Schema Consistency Check
    if schema_context and schema_context.tables:
        valid_tables = schema_context.get_table_names()
        # Add tables from source AST if available
        if source_tables:
            for t in source_tables:
                if isinstance(t, dict) and "name" in t:
                    valid_tables.add(t["name"].lower())

        referenced_tables = {
            table.name.lower()
            for table in parsed.find_all(exp.Table)
            if table.name
        }

        unknown_tables = referenced_tables - valid_tables
        if unknown_tables:
            table_list = ", ".join(sorted(unknown_tables))
            return (
                CandidateValidationStatus.SCHEMA_MISMATCH,
                "UNKNOWN_TABLE",
                f"Candidate SQL references table(s) not in supplied schema context: {table_list}",
            )

        # Column consistency check
        valid_columns = schema_context.get_column_names()
        if source_columns:
            for c in source_columns:
                if isinstance(c, dict) and "name" in c:
                    valid_columns.add(c["name"].lower())

        referenced_columns = {
            col.name.lower()
            for col in parsed.find_all(exp.Column)
            if col.name and col.name != "*"
        }

        # Filter out obvious aliases or CTE identifiers
        cte_aliases = {
            cte.alias.lower() for cte in parsed.find_all(exp.CTE) if cte.alias
        }
        unknown_columns = (referenced_columns - valid_columns) - cte_aliases
        if unknown_columns and len(valid_columns) > 0:
            col_list = ", ".join(sorted(unknown_columns))
            return (
                CandidateValidationStatus.SCHEMA_MISMATCH,
                "UNKNOWN_COLUMN",
                f"Candidate SQL references column(s) not in supplied schema context: {col_list}",
            )

    return (
        CandidateValidationStatus.VALID_SYNTAX,
        "",
        "Candidate SQL syntactically valid",
    )
