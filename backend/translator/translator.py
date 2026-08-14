import sqlglot
from backend.core.exceptions import TranslationException
from backend.core.logging import logger
from backend.core.models import Dialect
from backend.translator.schemas import TranslationResult, TranslationTask


class SQLTranslator:
    """Translates SQL queries across database dialects using AST transpilation."""

    @staticmethod
    def translate(task: TranslationTask) -> TranslationResult:
        """Transpile SQL from source_dialect to target_dialect."""
        try:
            read_dialect = task.source_dialect.value
            write_dialect = task.target_dialect.value

            # Map sqlite/duckdb/postgres appropriately
            transpiled = sqlglot.transpile(
                task.source_sql,
                read=read_dialect,
                write=write_dialect,
                pretty=True
            )

            if not transpiled:
                raise TranslationException("Transpilation returned empty result")

            return TranslationResult(
                translated_sql=transpiled[0],
                source_dialect=task.source_dialect,
                target_dialect=task.target_dialect,
                used_llm_fallback=False,
                notes=[f"Direct AST transpilation from {read_dialect} to {write_dialect}"]
            )
        except Exception as e:
            logger.warning(f"AST Transpilation failed: {str(e)}. Falling back to rule-based fallback.")
            # Simple heuristic rule-based replacement as fallback
            fallback_sql = task.source_sql
            if task.source_dialect == Dialect.ORACLE and task.target_dialect == Dialect.POSTGRES:
                fallback_sql = fallback_sql.replace("NVL(", "COALESCE(").replace("SYSDATE", "CURRENT_TIMESTAMP")
            elif task.source_dialect == Dialect.SNOWFLAKE and task.target_dialect == Dialect.BIGQUERY:
                fallback_sql = fallback_sql.replace("IFF(", "IF(")

            return TranslationResult(
                translated_sql=fallback_sql,
                source_dialect=task.source_dialect,
                target_dialect=task.target_dialect,
                used_llm_fallback=True,
                notes=[f"Transpilation fallback applied: {str(e)}"]
            )
