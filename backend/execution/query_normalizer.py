"""Query normalization and read-only SQL security validation using SQLGlot."""

import sqlglot
from sqlglot import exp

from backend.execution.exceptions import SecurityViolationError


def normalize_query_sql(sql: str) -> str:
    """Conservatively normalize SQL query text for hashing and auditability.

    Normalizes whitespace and line endings without semantic rewrites.
    """
    cleaned = sql.strip()
    if not cleaned:
        return ""
    # Normalize CRLF to LF and collapse consecutive blank lines
    lines = [line.rstrip() for line in cleaned.splitlines()]
    return "\n".join(lines)


# Statement types that are strictly forbidden in read-only analytical executions
UNSAFE_EXPRESSIONS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.Command,
)

FORBIDDEN_KEYWORDS = {"ATTACH", "DETACH", "COPY", "INSTALL", "LOAD", "EXPORT"}


def validate_read_only_query(sql: str) -> None:
    """Enforce read-only policy on submitted SQL.

    Raises SecurityViolationError if the SQL contains mutating or administrative statements.
    """
    normalized = sql.strip()
    if not normalized:
        raise SecurityViolationError("Empty SQL query submitted.")

    # Check for forbidden keywords in raw SQL
    upper_sql = normalized.upper()
    for kw in FORBIDDEN_KEYWORDS:
        # Match as whole word token
        tokens = upper_sql.replace(";", " ").split()
        if kw in tokens:
            raise SecurityViolationError(f"Forbidden SQL operation '{kw}' detected.")

    try:
        parsed = sqlglot.parse_one(normalized)
    except Exception as exc:
        # If parsing fails, fall back to keyword checks
        if any(
            verb in upper_sql
            for verb in ["INSERT ", "UPDATE ", "DELETE ", "DROP ", "CREATE ", "ALTER "]
        ):
            raise SecurityViolationError("Mutating SQL statement detected.") from exc
        return

    if parsed is None:
        raise SecurityViolationError("Unable to parse submitted SQL statement.")

    # Walk AST to verify no forbidden expressions exist
    for node in parsed.walk():
        if isinstance(node, UNSAFE_EXPRESSIONS):
            op_name = type(node).__name__.upper()
            raise SecurityViolationError(f"Mutating or DDL SQL operation '{op_name}' is forbidden.")
