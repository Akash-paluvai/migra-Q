"""Unit tests for LLM provider abstraction and Mock provider."""

import pytest

from backend.core.exceptions import ProviderExecutionTimeoutError
from backend.translator.context_builder import build_translation_context
from backend.translator.models import TranslationRequest
from backend.translator.prompts import build_translation_prompt
from backend.translator.provider import MockLLMProvider, OpenAIProvider, get_llm_provider


def test_mock_provider_good_mode():
    req = TranslationRequest(source_sql="SELECT * FROM transactions;")
    ctx = build_translation_context(req)
    sys_p, user_p, _ = build_translation_prompt(ctx)

    provider = MockLLMProvider(mode="MOCK_GOOD")
    raw_resp = provider.generate_translation(ctx, sys_p, user_p)

    assert raw_resp.raw_json != ""
    assert "target_sql" in raw_resp.raw_json
    assert raw_resp.total_tokens == 400


def test_mock_provider_boundary_bug_mode():
    req = TranslationRequest(source_sql="SELECT * FROM transactions WHERE amount > 500;")
    ctx = build_translation_context(req)
    sys_p, user_p, _ = build_translation_prompt(ctx)

    provider = MockLLMProvider(mode="MOCK_BOUNDARY_BUG")
    raw_resp = provider.generate_translation(ctx, sys_p, user_p)

    assert ">= 500.00" in raw_resp.raw_json


def test_mock_provider_hallucinated_column_mode():
    req = TranslationRequest(source_sql="SELECT * FROM transactions;")
    ctx = build_translation_context(req)
    sys_p, user_p, _ = build_translation_prompt(ctx)

    provider = MockLLMProvider(mode="MOCK_HALLUCINATED_COLUMN")
    raw_resp = provider.generate_translation(ctx, sys_p, user_p)

    assert "nonexistent_column" in raw_resp.raw_json


def test_mock_provider_unsafe_sql_mode():
    req = TranslationRequest(source_sql="SELECT * FROM transactions;")
    ctx = build_translation_context(req)
    sys_p, user_p, _ = build_translation_prompt(ctx)

    provider = MockLLMProvider(mode="MOCK_UNSAFE_SQL")
    raw_resp = provider.generate_translation(ctx, sys_p, user_p)

    assert "DROP TABLE" in raw_resp.raw_json


def test_mock_provider_timeout_raises():
    req = TranslationRequest(source_sql="SELECT 1;")
    ctx = build_translation_context(req)
    provider = MockLLMProvider(mode="MOCK_TIMEOUT")

    with pytest.raises(ProviderExecutionTimeoutError):
        provider.generate_translation(ctx, "sys", "user")


def test_mock_provider_auth_error_raises():
    req = TranslationRequest(source_sql="SELECT 1;")
    ctx = build_translation_context(req)
    provider = MockLLMProvider(mode="MOCK_AUTH_ERROR")

    with pytest.raises(PermissionError):
        provider.generate_translation(ctx, "sys", "user")


def test_get_llm_provider_factory():
    p = get_llm_provider(provider_name="mock", mock_mode="MOCK_GOOD")
    assert isinstance(p, MockLLMProvider)


def test_get_llm_provider_unknown_raises():
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        get_llm_provider(provider_name="unknown_provider")


def test_openai_provider_missing_model_raises(monkeypatch):
    monkeypatch.setattr("backend.core.config.settings.LLM_PROVIDER", "openai")
    monkeypatch.setattr("backend.core.config.settings.LLM_MODEL", "")
    monkeypatch.setattr("backend.core.config.settings.LLM_API_KEY", "sk-fake")

    with pytest.raises(ValueError, match="OpenAI model name must be provided"):
        OpenAIProvider()
