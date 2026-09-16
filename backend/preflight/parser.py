"""SQL Parser for Semantic Preflight.

Parses SQL text into a sqlglot AST, generating structured diagnostics for syntax errors.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

import sqlglot
from sqlglot import exp

@dataclass
class ParseResult:
    ast: Optional[exp.Expression]
    error_message: Optional[str]
    is_success: bool


def parse_sql(sql: str, dialect: str) -> ParseResult:
    """Parse SQL into an AST, capturing any syntax errors."""
    try:
        # read=dialect.lower() tells sqlglot which SQL dialect's rules to use
        # parse_one parses exactly one statement. If multiple are passed, it might fail or return the first.
        # We assume Migra-Q validates single statements (or the primary statement).
        ast = sqlglot.parse_one(sql, read=dialect.lower())
        return ParseResult(ast=ast, error_message=None, is_success=True)
    except Exception as e:
        return ParseResult(ast=None, error_message=str(e), is_success=False)
