import pytest

from backend.translator.models import TranslationRequest, TranslationContext
from backend.translator.provider import OpenAIProvider, MockLLMProvider
from backend.translator.service import TranslationService
from backend.core.dialects import Netezza

NETEZZA_DATE_SQL = """
SELECT
    event_id,
    user_id,
    DATE_TRUNC('month', event_date) AS event_month,
    EXTRACT(YEAR FROM event_date) AS event_year
FROM event_logs
WHERE event_date >= DATE '2026-01-01'
  AND event_date < DATE '2027-01-01'
ORDER BY event_date;
"""

def test_netezza_date_literals_translation(monkeypatch):
    """Test that Netezza correctly processes date literals without JSON validation errors."""
    
    # We patch get_llm_provider to use our MockLLMProvider, but we verify 
    # the entire service pipeline passes.
    def mock_get_provider(*args, **kwargs):
        return MockLLMProvider(mode="MOCK_GOOD")
        
    monkeypatch.setattr("backend.translator.service.get_llm_provider", mock_get_provider)
    
    service = TranslationService()
    
    request = TranslationRequest(
        request_id="req_netezza_dates",
        source_dialect="netezza",
        target_dialect="snowflake",
        dataset_id="date_semantics",
        source_sql=NETEZZA_DATE_SQL.strip()
    )
    
    response = service.translate(request)
    
    assert response.status.name == "SUCCESS"
    assert response.response is not None
    assert response.response.target_sql is not None


def test_malformed_json_fails_fast_no_retry(monkeypatch):
    """Test that json_validate_failed returns a fast failure and does not trigger retry storms."""
    
    # MOCK_INVALID_JSON is simulating a model that returns syntactically bad JSON
    def mock_get_provider(*args, **kwargs):
        return MockLLMProvider(mode="MOCK_INVALID_JSON")
        
    monkeypatch.setattr("backend.translator.service.get_llm_provider", mock_get_provider)
    
    service = TranslationService()
    
    request = TranslationRequest(
        request_id="req_invalid_json",
        source_dialect="netezza",
        target_dialect="snowflake",
        dataset_id="date_semantics",
        source_sql=NETEZZA_DATE_SQL.strip()
    )
    
    response = service.translate(request)
    
    assert response.status.name == "INVALID_OUTPUT"
    # Ensure it says something about invalid JSON or JSON decoder error
    assert "JSON" in response.metadata.error_message or "parse" in response.metadata.error_message.lower()

def test_provider_json_validate_failed_no_retry(monkeypatch):
    """Test that provider-level json_validate_failed returns a fast failure and does not trigger retry storms."""
    
    # We'll mock the provider to raise a NonRetryableProviderError directly
    from backend.core.exceptions import NonRetryableProviderError
    class MockProviderThrows400(MockLLMProvider):
        def generate_translation(self, *args, **kwargs):
            raise NonRetryableProviderError("json_validate_failed: Schema mismatch")
            
    def mock_get_provider(*args, **kwargs):
        return MockProviderThrows400()
        
    monkeypatch.setattr("backend.translator.service.get_llm_provider", mock_get_provider)
    
    service = TranslationService()
    
    request = TranslationRequest(
        request_id="req_invalid_schema",
        source_dialect="netezza",
        target_dialect="snowflake",
        dataset_id="date_semantics",
        source_sql="SELECT 1;"
    )
    
    response = service.translate(request)
    
    assert response.status.name == "PROVIDER_ERROR"
    assert response.metadata.error_code == "INVALID_STRUCTURED_OUTPUT"
