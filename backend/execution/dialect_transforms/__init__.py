"""DuckDB compatibility adapter registry with capability/confidence analysis.

Pipeline:
    Source SQL
        -> SQLGlot parse (source dialect)
        -> AST
        -> analyze_and_transform() [this module]
            -> Dialect adapter (per-node CompatibilityResult)
            -> Common sandbox rules
            -> Aggregate confidence + diagnostics
        -> CompatibilityAnalysis
        -> duckdb_runner decides whether to execute
"""

import sqlglot.expressions as exp

from .base import (
    CompatibilityAnalysis,
    CompatibilityResult,
    DialectCompatibilityAdapter,
    SemanticConfidence,
)
from .bigquery import BigQueryAdapter
from .common import transform_common_sandbox_rules
from .netezza import NetezzaAdapter
from .oracle import OracleAdapter
from .snowflake import SnowflakeAdapter
from .teradata import TeradataAdapter

# ── Adapter Registry ──────────────────────────────────────────────
_ADAPTERS: dict[str, type[DialectCompatibilityAdapter]] = {
    "oracle": OracleAdapter,
    "teradata": TeradataAdapter,
    "bigquery": BigQueryAdapter,
    "snowflake": SnowflakeAdapter,
    "netezza": NetezzaAdapter,
}


def analyze_and_transform(parsed: exp.Expression, dialect: str) -> CompatibilityAnalysis:
    """Walk the AST, apply adapter + common transforms, aggregate confidence.

    Returns a CompatibilityAnalysis that the runner uses to decide
    whether to execute and what confidence to attach to the result.
    """
    adapter_cls = _ADAPTERS.get(dialect, DialectCompatibilityAdapter)
    confidences: list[SemanticConfidence] = []
    all_diagnostics: list[dict] = []
    all_executable = True

    def _per_node(node: exp.Expression) -> exp.Expression:
        nonlocal all_executable

        # 1. Dialect-specific adapter
        result = adapter_cls.transform(node)
        confidences.append(result.confidence)
        all_diagnostics.extend(result.diagnostics)
        if not result.executable:
            all_executable = False
        out_node = result.transformed_node

        # 2. Common sandbox rules (catalog/db stripping)
        out_node = transform_common_sandbox_rules(out_node)

        return out_node

    transformed = parsed.transform(_per_node)

    # Aggregate: max confidence across all nodes (highest semantic risk)
    aggregate = SemanticConfidence.EXACT
    for c in confidences:
        if c > aggregate:
            aggregate = c

    return CompatibilityAnalysis(
        transformed_ast=transformed,
        aggregate_confidence=aggregate,
        executable=all_executable,
        diagnostics=all_diagnostics,
    )


# Backward-compatible wrapper used by the old transform path.
def transform_for_duckdb(node: exp.Expression, dialect: str) -> exp.Expression:
    """Legacy single-node transform. Used by parsed.transform(lambda)."""
    adapter_cls = _ADAPTERS.get(dialect, DialectCompatibilityAdapter)
    result = adapter_cls.transform(node)
    out = result.transformed_node
    out = transform_common_sandbox_rules(out)
    return out
