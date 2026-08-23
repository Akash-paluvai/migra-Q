"""BigQuery -> DuckDB compatibility adapter.

Transforms:
- ARRAY_AGG(val ORDER BY col LIMIT 1)[OFFSET(0)] -> arg_min/arg_max  [SAFE_EQUIVALENT]
"""

import sqlglot.expressions as exp

from .base import CompatibilityResult, DialectCompatibilityAdapter, SemanticConfidence


class BigQueryAdapter(DialectCompatibilityAdapter):
    """Compatibility adapter for BigQuery -> DuckDB."""

    @staticmethod
    def transform(node: exp.Expression) -> CompatibilityResult:
        if isinstance(node, exp.Bracket):
            inner = node.this
            if isinstance(inner, exp.Paren):
                inner = inner.this

            if isinstance(inner, (exp.GroupConcat, exp.ArrayAgg)):
                limit_node = inner.this
                if isinstance(limit_node, exp.Limit):
                    order_node = limit_node.this
                    if isinstance(order_node, exp.Order):
                        val_col = order_node.this
                        order_exp = order_node.expressions[0]
                        order_col = order_exp.this
                        is_desc = order_exp.args.get("desc")

                        limit_val = limit_node.expression.name if hasattr(limit_node.expression, "name") else str(limit_node.expression)
                        if limit_val == "1":
                            func_name = "arg_max" if is_desc else "arg_min"
                            return CompatibilityResult(
                                executable=True,
                                confidence=SemanticConfidence.SAFE_EQUIVALENT,
                                transformed_node=exp.Anonymous(this=func_name, expressions=[val_col, order_col]),
                            )

        return CompatibilityResult(
            executable=True,
            confidence=SemanticConfidence.EXACT,
            transformed_node=node,
        )
