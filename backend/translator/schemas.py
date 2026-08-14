from pydantic import BaseModel
from backend.core.models import Dialect


class TranslationTask(BaseModel):
    source_sql: str
    source_dialect: Dialect
    target_dialect: Dialect


class TranslationResult(BaseModel):
    translated_sql: str
    source_dialect: Dialect
    target_dialect: Dialect
    used_llm_fallback: bool = False
    notes: list[str] = []
