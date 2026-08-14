from sqlglot import exp, diff
from backend.core.models import ASTDiffResult


class ASTDiffEngine:
    """Computes structural AST diffs between source and target SQL expressions."""

    @staticmethod
    def compare_ast(source_expr: exp.Expression, target_expr: exp.Expression) -> ASTDiffResult:
        """Compute node-level diffs and structural changes between two ASTs."""
        differences = diff(source_expr, target_expr)
        
        changes = []
        for d in differences:
            changes.append(f"{d.__class__.__name__}: {str(d)}")

        source_count = len(list(source_expr.walk()))
        target_count = len(list(target_expr.walk()))
        delta = (target_count - source_count) / max(source_count, 1)

        return ASTDiffResult(
            source_ast_summary=f"{source_expr.key.upper()} with {source_count} nodes",
            target_ast_summary=f"{target_expr.key.upper()} with {target_count} nodes",
            structural_changes=changes[:10],
            complexity_delta=round(delta, 3)
        )
