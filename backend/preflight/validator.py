"""Schema Preflight Validator.

Deterministically validates source SQL against the dataset schema before execution,
using a SQL compiler semantic name resolution phase.
"""

from __future__ import annotations
from typing import List

from backend.assurance.models import PreflightSummary
from backend.core.logging import get_logger
from backend.preflight.parser import parse_sql
from backend.preflight.semantic import resolve_semantics

logger = get_logger(__name__)


class SchemaPreflightValidator:
    """Validates SQL table and column references against the target dataset schema."""

    @classmethod
    def validate(cls, sql: str, dataset_id: str, dialect: str = "teradata") -> PreflightSummary:
        """Parse SQL and ensure all referenced tables and columns exist in the dataset."""
        
        # 1. Parse Phase
        parse_result = parse_sql(sql, dialect)
        if not parse_result.is_success or not parse_result.ast:
            # Note: We return PASS with execution_allowed=True if parsing fails,
            # allowing DuckDB execution to handle raw syntax errors gracefully.
            # Alternatively, we could BLOCK on parse errors. For now, we only 
            # block on semantic resolution errors.
            logger.warning(f"Schema preflight skipped due to parse error: {parse_result.error_message}")
            return PreflightSummary(status="PASS", execution_allowed=True)

        # 2. Semantic Name Resolution Phase
        diagnostics = resolve_semantics(parse_result.ast, dialect, dataset_id)
        
        # 3. Diagnostic Reporting
        if diagnostics:
            # We have a schema or semantic mismatch. Halt execution.
            diagnostic = diagnostics[0]
            
            # Format a nice message for the diagnostic
            reason = f"[{diagnostic.code}] {diagnostic.message}"
            
            return PreflightSummary(
                status="FAILED",
                failure_category="INPUT_SCHEMA_MISMATCH",
                execution_allowed=False,
                unresolved_tables=[], # We don't necessarily extract them individually anymore since sqlglot does the work
                reason=reason,
                available_columns=diagnostic.available_columns or {}
            )

        # 4. Validation Passed
        return PreflightSummary(status="PASS", execution_allowed=True)
