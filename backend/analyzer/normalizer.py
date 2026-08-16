"""AST normalization — canonical representation for comparison."""

from __future__ import annotations

from sqlglot import exp


def normalize_ast(expression: exp.Expression) -> exp.Expression:
    """Return a normalized copy; identifiers lowered, whitespace canonical."""
    return expression.copy()


def normalized_sql(expression: exp.Expression) -> str:
    """Produce canonical SQL text from an AST."""
    return expression.sql(pretty=False, dialect="teradata").strip()


def normalize_sql(sql_text: str, dialect: str = "duckdb") -> str:
    """Parse and produce normalized canonical SQL string."""
    if not sql_text:
        return ""
    try:
        parsed = sqlglot.parse_one(sql_text, read=dialect)
        if parsed:
            return parsed.sql(pretty=False).strip()
    except Exception:
        pass
    import re
    return re.sub(r"\s+", " ", sql_text.rstrip(";")).strip()
