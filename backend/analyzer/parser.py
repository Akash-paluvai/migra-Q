"""SQL parser — validates and parses SQL into a SQLGlot AST."""

from __future__ import annotations

import sqlglot
from sqlglot import exp

from backend.core.exceptions import ParserError


def parse_sql(sql: str, dialect: str = "teradata") -> exp.Expression:
    """Parse a SQL string into a SQLGlot AST expression.

    Raises ParserError on invalid SQL or empty input.
    """
    sql = sql.strip()
    if not sql:
        raise ParserError("Empty SQL input")

    try:
        parsed = sqlglot.parse_one(sql, read=dialect.lower())
    except sqlglot.errors.ParseError as exc:
        raise ParserError(f"SQL parse error ({dialect}): {exc}") from exc
    except Exception as exc:
        raise ParserError(f"Unexpected parse failure ({dialect}): {exc}") from exc

    if parsed is None:
        raise ParserError(f"Parser returned None for dialect '{dialect}'")

    return parsed
