"""
SQL Translator package for dialect translation via sqlglot and LLM assistance.
"""
from backend.translator.translator import SQLTranslator
from backend.translator.prompts import PROMPT_SQL_TRANSLATION, PROMPT_REPAIR_SQL
from backend.translator.schemas import TranslationTask, TranslationResult

__all__ = ["SQLTranslator", "PROMPT_SQL_TRANSLATION", "PROMPT_REPAIR_SQL", "TranslationTask", "TranslationResult"]
