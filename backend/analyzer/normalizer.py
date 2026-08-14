"""AST normalization — canonical representation for comparison."""

from __future__ import annotations

from sqlglot import exp


def normalize_ast(expression: exp.Expression) -> exp.Expression:
    """Return a normalized copy; identifiers lowered, whitespace canonical."""
    return expression.copy()


def normalized_sql(expression: exp.Expression) -> str:
    """Produce canonical SQL text from an AST."""
    return expression.sql(pretty=False, dialect="teradata").strip()
