"""Snowflake -> DuckDB compatibility adapter.

Transforms:
- TO_VARCHAR(number, numeric_mask) -> CAST(number AS VARCHAR)  [APPROXIMATION]
- TO_VARCHAR(timestamp, date_mask) -> strftime(timestamp, fmt)  [SAFE_EQUIVALENT]
"""

import sqlglot.expressions as exp

from .base import CompatibilityResult, DialectCompatibilityAdapter, SemanticConfidence


class SnowflakeAdapter(DialectCompatibilityAdapter):
    """Compatibility adapter for Snowflake -> DuckDB."""

    @staticmethod
    def transform(node: exp.Expression) -> CompatibilityResult:
        if isinstance(node, exp.ToChar):
            format_val = node.args.get("format")
            if format_val and isinstance(format_val, exp.Literal) and format_val.is_string:
                fmt_str = format_val.this

                if any(c in fmt_str for c in "90,.$"):
                    # Numeric formatting mask -> CAST. Formatting lost.
                    return CompatibilityResult(
                        executable=True,
                        confidence=SemanticConfidence.APPROXIMATION,
                        transformed_node=exp.Cast(
                            this=node.this, to=exp.DataType.build("VARCHAR")
                        ),
                        diagnostics=[{
                            "transform": "TO_VARCHAR_NUMERIC",
                            "confidence": "APPROXIMATION",
                            "reason": "Numeric formatting mask semantics are not preserved in DuckDB CAST.",
                        }],
                    )

                # Date/time mask -> strftime.
                new_fmt = fmt_str.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
                new_fmt = new_fmt.replace("yyyy", "%Y").replace("mm", "%m").replace("dd", "%d")
                return CompatibilityResult(
                    executable=True,
                    confidence=SemanticConfidence.SAFE_EQUIVALENT,
                    transformed_node=exp.TimeToStr(
                        this=node.this, format=exp.Literal.string(new_fmt)
                    ),
                )

        return CompatibilityResult(
            executable=True,
            confidence=SemanticConfidence.EXACT,
            transformed_node=node,
        )
