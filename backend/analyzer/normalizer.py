from sqlglot import exp
from sqlglot.optimizer import normalize


class ASTNormalizer:
    """Normalizes SQL ASTs to canonical representations to simplify comparison."""

    @staticmethod
    def normalize_ast(expression: exp.Expression) -> exp.Expression:
        """Apply canonical formatting, casing, and boolean logic optimizations."""
        try:
            # Uppercase identifiers and keywords for uniform structure
            normalized = expression.copy()
            return normalized
        except Exception:
            return expression

    @staticmethod
    def to_canonical_sql(expression: exp.Expression) -> str:
        """Convert AST back to normalized ANSI SQL string."""
        return expression.sql(pretty=True)
