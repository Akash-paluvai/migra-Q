"""Netezza -> DuckDB compatibility adapter.

No proven compatibility gaps yet. Added when real migrations expose gaps.
"""

import sqlglot.expressions as exp

from .base import CompatibilityResult, DialectCompatibilityAdapter, SemanticConfidence


class NetezzaAdapter(DialectCompatibilityAdapter):
    """Compatibility adapter for Netezza -> DuckDB. No transforms yet."""

    @staticmethod
    def transform(node: exp.Expression) -> CompatibilityResult:
        return CompatibilityResult(
            executable=True,
            confidence=SemanticConfidence.EXACT,
            transformed_node=node,
        )
