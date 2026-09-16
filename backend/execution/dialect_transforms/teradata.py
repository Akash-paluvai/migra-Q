"""Teradata -> DuckDB compatibility adapter.

Transforms:
- ZEROIFNULL(x) -> COALESCE(x, 0)  [EXACT]
- NULLIFZERO(x) -> NULLIF(x, 0)    [EXACT]
"""

import sqlglot.expressions as exp

from .base import CompatibilityResult, DialectCompatibilityAdapter, SemanticConfidence


class TeradataAdapter(DialectCompatibilityAdapter):
    """Compatibility adapter for Teradata -> DuckDB."""

    @staticmethod
    def transform(node: exp.Expression) -> CompatibilityResult:
        if isinstance(node, exp.Anonymous):
            name = node.name.upper()
            if name == "ZEROIFNULL" and len(node.expressions) == 1:
                return CompatibilityResult(
                    executable=True,
                    confidence=SemanticConfidence.EXACT,
                    transformed_node=exp.Coalesce(
                        this=node.expressions[0],
                        expressions=[exp.Literal.number(0)],
                    ),
                )
            if name == "NULLIFZERO" and len(node.expressions) == 1:
                return CompatibilityResult(
                    executable=True,
                    confidence=SemanticConfidence.EXACT,
                    transformed_node=exp.Nullif(
                        this=node.expressions[0],
                        expression=exp.Literal.number(0),
                    ),
                )
        return CompatibilityResult(
            executable=True,
            confidence=SemanticConfidence.EXACT,
            transformed_node=node,
        )
