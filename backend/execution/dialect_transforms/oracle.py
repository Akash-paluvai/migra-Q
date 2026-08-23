"""Oracle -> DuckDB compatibility adapter.

Transforms:
- KEEP (DENSE_RANK FIRST/LAST ORDER BY col) -> arg_min/arg_max  [SAFE_EQUIVALENT]
"""

import sqlglot.expressions as exp

from .base import CompatibilityResult, DialectCompatibilityAdapter, SemanticConfidence


class OracleAdapter(DialectCompatibilityAdapter):
    """Compatibility adapter for Oracle -> DuckDB."""

    @staticmethod
    def transform(node: exp.Expression) -> CompatibilityResult:
        if isinstance(node, exp.Window) and isinstance(node.args.get("over"), str) and node.args.get("over").upper() == "KEEP":
            val_col = node.this.this if isinstance(node.this, (exp.Max, exp.Min)) else None
            order_node = node.args.get("order")
            if val_col and order_node and order_node.expressions:
                order_exp = order_node.expressions[0]
                order_col = order_exp.this
                is_desc = order_exp.args.get("desc") or False
                is_first = node.args.get("first") or False

                if is_first:
                    use_arg_max = is_desc
                else:
                    use_arg_max = not is_desc

                func_name = "arg_max" if use_arg_max else "arg_min"
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
