from backend.core.models import Dialect
from backend.translator.schemas import TranslationTask
from backend.translator.translator import SQLTranslator


def test_oracle_to_postgres_translation():
    task = TranslationTask(
        source_sql="SELECT NVL(amount, 0) FROM tx",
        source_dialect=Dialect.ORACLE,
        target_dialect=Dialect.POSTGRES
    )
    result = SQLTranslator.translate(task)
    assert "COALESCE" in result.translated_sql or "NVL" in result.translated_sql
