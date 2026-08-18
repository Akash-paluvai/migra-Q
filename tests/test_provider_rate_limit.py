import json
import time
import urllib.error
from unittest.mock import patch, MagicMock
import pytest

from backend.core.exceptions import ProviderTokenExhaustionError, RateLimitError, ProviderExecutionTimeoutError
from backend.translator.provider import OpenAIProvider
from backend.translator.models import TranslationContext

def test_provider_token_exhaustion_no_retry():
    provider = OpenAIProvider()
    provider.model = "groq-model"
    context = TranslationContext(
        source_sql="SELECT 1", 
        normalized_sql="SELECT 1", 
        source_dialect="oracle", 
        target_dialect="bigquery", 
        tables=[], 
        columns=[], 
        schema_name=""
    )
    
    # Mock the HTTP response for Groq 429 TPD
    error_body = {
        "error": {
            "message": "Rate limit reached for model `llama-3.1-8b-instant` in organization `org_id` on tokens per day (TPD): Limit 200000, Used 200000, Requested 4000.",
            "type": "tokens",
            "code": "rate_limit_exceeded"
        }
    }
    
    mock_http_error = urllib.error.HTTPError(
        url="http://mock",
        code=429,
        msg="Too Many Requests",
        hdrs={"retry-after": "1000"},
        fp=MagicMock()
    )
    mock_http_error.read = MagicMock(return_value=json.dumps(error_body).encode("utf-8"))
    
    with patch("urllib.request.urlopen") as mock_urlopen, \
         patch("time.sleep") as mock_sleep:
        mock_urlopen.side_effect = mock_http_error
        
        with pytest.raises(ProviderTokenExhaustionError) as exc_info:
            provider.generate_translation(context, "sys", "user")
            
        assert exc_info.value.retry_after == 1000.0
        assert mock_urlopen.call_count == 1  # Exactly 1 attempt, NO RETRIES!

@patch("backend.translator.provider.settings.LLM_MAX_RETRIES", 2)
def test_provider_transient_rate_limit_retry():
    provider = OpenAIProvider()
    provider.model = "groq-model"
    context = TranslationContext(
        source_sql="SELECT 1", 
        normalized_sql="SELECT 1", 
        source_dialect="oracle", 
        target_dialect="bigquery", 
        tables=[], 
        columns=[], 
        schema_name=""
    )
    
    # Mock a transient 429 (not token exhaustion)
    error_body = {
        "error": {
            "message": "Rate limit reached... Requests Per Minute (RPM)",
            "type": "requests",
            "code": "rate_limit_exceeded"
        }
    }
    
    mock_http_error = urllib.error.HTTPError(
        url="http://mock",
        code=429,
        msg="Too Many Requests",
        hdrs={"retry-after": "0.1"},
        fp=MagicMock()
    )
    mock_http_error.read = MagicMock(return_value=json.dumps(error_body).encode("utf-8"))
    
    with patch("urllib.request.urlopen") as mock_urlopen, \
         patch("time.sleep") as mock_sleep:
        
        mock_urlopen.side_effect = mock_http_error
        
        with pytest.raises(RateLimitError):
            provider.generate_translation(context, "sys", "user")
            
        assert mock_urlopen.call_count == 2  # Retried up to max retries
