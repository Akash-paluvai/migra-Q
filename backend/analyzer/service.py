"""AnalyzerService — single entry point used by both CLI and API.

Has ZERO dependency on PostgreSQL / FastAPI / LLMs.
"""

from __future__ import annotations

from backend.analyzer.models import SQLAnalysis
from backend.analyzer.normalizer import normalize_ast, normalized_sql
from backend.analyzer.parser import parse_sql
from backend.analyzer.rule_extractor import (
    _reset_counters,
    detect_warnings,
    extract_aggregations,
    extract_case_expressions,
    extract_columns,
    extract_filters,
    extract_joins,
    extract_null_sensitive,
    extract_tables,
)


def analyze(sql: str, dialect: str = "teradata") -> SQLAnalysis:
    """Parse and analyze a single SQL statement.

    Returns a fully populated SQLAnalysis.  Never touches the database.
    """
    _reset_counters()

    tree = parse_sql(sql, dialect)
    norm_tree = normalize_ast(tree)
    norm = normalized_sql(norm_tree)
    sql_hash = SQLAnalysis.compute_hash(norm)

    tables = extract_tables(tree)
    columns = extract_columns(tree)
    joins = extract_joins(tree)
    filters = extract_filters(tree)
    aggregations = extract_aggregations(tree)
    case_exprs, business_rules = extract_case_expressions(tree)
    null_sensitive = extract_null_sensitive(tree)
    warnings = detect_warnings(tree)

    return SQLAnalysis(
        dialect=dialect,
        original_sql=sql.strip(),
        normalized_sql=norm,
        sql_hash=sql_hash,
        tables=tables,
        columns=columns,
        joins=joins,
        filters=filters,
        aggregations=aggregations,
        case_expressions=case_exprs,
        business_rules=business_rules,
        null_sensitive_expressions=null_sensitive,
        warnings=warnings,
    )


class AnalyzerService:
    """Class wrapper for AnalyzerService."""

    @staticmethod
    def analyze(sql: str, dialect: str = "teradata") -> SQLAnalysis:
        return analyze(sql, dialect)
