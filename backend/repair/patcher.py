from typing import Tuple


class SQLPatcher:
    """Modifies AST / raw SQL string targets to fix identified mismatches."""

    @staticmethod
    def patch_missing_columns(sql: str, missing_cols: list[str]) -> Tuple[str, str]:
        if not missing_cols:
            return sql, "No missing columns specified"

        cols_str = ", ".join(missing_cols)
        explanation = f"Added missing projection columns: {cols_str}"
        # Replace SELECT with SELECT missing_cols, if simple
        if sql.strip().upper().startswith("SELECT "):
            patched = "SELECT " + cols_str + ", " + sql.strip()[7:]
            return patched, explanation

        return sql, explanation

    @staticmethod
    def patch_null_semantics(sql: str) -> Tuple[str, str]:
        patched = sql.replace("NVL(", "COALESCE(")
        return patched, "Replaced dialect NVL with ANSI standard COALESCE"
