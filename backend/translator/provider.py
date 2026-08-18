"""LLM Provider abstraction layer — defines interface, OpenAI provider, and Mock provider."""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from backend.core.config import settings
from backend.core.exceptions import (
    NonRetryableProviderError,
    ProviderError,
    ProviderExecutionTimeoutError,
    ProviderTokenExhaustionError,
    RateLimitError,
    TransientProviderError,
)
from backend.translator.models import TranslationContext


@dataclass
class RawProviderResponse:
    """Raw response output container from an LLM provider call."""

    raw_json: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    duration_ms: float = 0.0
    provider_attempts: int = 1


def _clean_json_response(raw_text: str) -> str:
    """Strip markdown codeblock wrappers if LLM returned ```json ... ```."""
    text = raw_text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
        
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end+1]
            
    return text


class LLMProvider(ABC):
    """Abstract interface for LLM generative translation providers."""

    @abstractmethod
    def generate_translation(
        self,
        context: TranslationContext,
        system_prompt: str,
        user_prompt: str,
    ) -> RawProviderResponse:
        """Invoke LLM provider and return raw structured JSON output."""
        pass


class MockLLMProvider(LLMProvider):
    """Deterministic Mock LLM Provider for 100% offline, zero-network unit testing."""

    def __init__(self, mode: str = "MOCK_GOOD"):
        self.mode = mode

    def generate_translation(
        self,
        context: TranslationContext,
        system_prompt: str,
        user_prompt: str,
    ) -> RawProviderResponse:
        """Return deterministic mock responses based on configured scenario mode."""
        start_time = time.perf_counter()

        if self.mode == "MOCK_TIMEOUT":
            raise ProviderExecutionTimeoutError("Global execution timeout exceeded during LLM retries.")

        if self.mode in ("MOCK_AUTH_ERROR", "AUTH_ERROR"):
            raise PermissionError("Authentication failed: invalid API key.")

        if self.mode in ("MOCK_PROVIDER_ERROR", "PROVIDER_ERROR"):
            raise RuntimeError("LLM provider internal error.")

        if self.mode == "MOCK_TOKEN_EXHAUSTION":
            raise ProviderTokenExhaustionError("LLM provider daily token limit exhausted.", retry_after=2040)

        if self.mode in ("MOCK_RATE_LIMIT", "RATE_LIMIT"):
            raise RateLimitError("HTTP 429 Rate Limit Exceeded (Max Retries Reached)")

        if self.mode == "MOCK_TRANSIENT_429":
            # Simulate 2 retries then success
            target_sql = "SELECT 'transient_recovery' AS status;"
            payload = {
                "target_sql": target_sql,
                "assumptions": ["Recovered after transient 429"],
                "potential_risks": [],
                "translated_rules": [],
            }
            return RawProviderResponse(
                raw_json=json.dumps(payload),
                input_tokens=100,
                output_tokens=20,
                total_tokens=120,
                duration_ms=(time.perf_counter() - start_time) * 1000.0,
                provider_attempts=3,
            )

        if self.mode == "MOCK_INVALID_JSON":
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return RawProviderResponse(
                raw_json="INVALID_JSON_RAW_TEXT{{{",
                input_tokens=100,
                output_tokens=20,
                total_tokens=120,
                duration_ms=duration_ms,
                provider_attempts=1,
            )

        if self.mode == "MOCK_UNSAFE_SQL":
            payload = {
                "target_sql": "DROP TABLE customers;",
                "assumptions": ["Mock unsafe mutation"],
                "potential_risks": ["Destructive statement"],
                "translated_rules": [],
            }
        elif self.mode == "MOCK_BOUNDARY_BUG":
            # Valid candidate with subtle boundary condition bug (> 500 -> >= 500)
            payload = {
                "target_sql": """SELECT
  c.customer_id,
  c.customer_segment,
  SUM(t.amount) AS total_amount,
  CASE WHEN t.amount >= 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;""",
                "assumptions": ["Assumed BigQuery dialect syntax"],
                "potential_risks": ["Boundary condition operator changed to >="],
                "translated_rules": [
                    {
                        "source_path": "business_rules[0]",
                        "source_expression": "t.amount > 500",
                        "target_expression": "t.amount >= 500",
                        "rule_type": "comparison",
                    }
                ],
            }
        elif self.mode == "MOCK_SEMANTICALLY_WRONG":
            # Valid candidate with multiple structural/aggregation semantic changes
            payload = {
                "target_sql": """SELECT
  c.customer_id,
  c.customer_segment,
  SUM(t.amount) AS total_amount,
  CASE WHEN SUM(t.amount) > 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment
ORDER BY c.customer_id;""",
                "assumptions": ["Grouped BY customer_id and customer_segment"],
                "potential_risks": [
                    "t.amount removed from GROUP BY",
                    "Aggregation SUM(t.amount) introduced inside CASE expression",
                ],
                "translated_rules": [
                    {
                        "source_path": "business_rules[0]",
                        "source_expression": "t.amount > 500",
                        "target_expression": "SUM(t.amount) > 500.00",
                        "rule_type": "comparison",
                    }
                ],
            }
        elif self.mode == "MOCK_HALLUCINATED_COLUMN":
            payload = {
                "target_sql": "SELECT customer_id, nonexistent_column FROM transactions;",
                "assumptions": ["Used hallucinated column"],
                "potential_risks": ["Column does not exist"],
                "translated_rules": [],
            }
        else:  # Default MOCK_GOOD (Genuinely structurally faithful to source query!)
            if "Ignore" in context.source_sql or "DROP TABLE" in context.source_sql:
                if "customer_id" in context.source_sql:
                    target_sql = "SELECT customer_id FROM transactions;"
                else:
                    target_sql = "SELECT 'data' AS message FROM transactions;"
            elif "customer_segment" in context.source_sql and "customer_risk" in (getattr(context, "dataset_id", "") or ""):
                target_sql = """SELECT
  c.customer_id,
  c.customer_segment,
  SUM(t.amount) AS total_amount,
  CASE WHEN t.amount > 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;"""
            else:
                try:
                    import sqlglot
                    transpiled = sqlglot.transpile(
                        context.source_sql,
                        read=context.source_dialect,
                        write=context.target_dialect,
                    )
                    target_sql = transpiled[0] if transpiled else context.source_sql
                except Exception:
                    target_sql = context.source_sql

            payload = {
                "target_sql": target_sql,
                "assumptions": ["Faithfully translated for target dialect"],
                "potential_risks": [],
                "translated_rules": [],
            }

        raw_json = json.dumps(payload)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return RawProviderResponse(
            raw_json=raw_json,
            input_tokens=250,
            output_tokens=150,
            total_tokens=400,
            duration_ms=duration_ms,
            provider_attempts=1,
        )


class OpenAIProvider(LLMProvider):
    """Production / OpenRouter provider calling OpenAI-compatible HTTP API via urllib."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ):
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        self.base_url = base_url or settings.LLM_BASE_URL or "https://openrouter.ai/api/v1"
        self.timeout = timeout or settings.LLM_TIMEOUT_SECONDS

        if not self.api_key:
            raise ValueError(
                "OpenAI API key must be provided or configured in settings.LLM_API_KEY."
            )
        if not self.model:
            raise ValueError(
                "OpenAI model name must be provided or configured in settings.LLM_MODEL."
            )

    def generate_translation(
        self,
        context: TranslationContext,
        system_prompt: str,
        user_prompt: str,
    ) -> RawProviderResponse:
        """Call OpenRouter / OpenAI chat completions API via urllib."""
        import json
        import urllib.error
        import urllib.request

        start_time = time.perf_counter()

        base_endpoint = self.base_url.rstrip("/")
        url = f"{base_endpoint}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "MIGRA-Q",
            "User-Agent": "MIGRA-Q/1.0",
        }
        body = {
            "model": self.model,
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_OUTPUT_TOKENS,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        # Dynamic Response Format Selection
        if "gpt-oss" in self.model or "gpt-4" in self.model:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "translation_response",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "target_sql": {"type": "string"},
                            "assumptions": {"type": "array", "items": {"type": "string"}},
                            "potential_risks": {"type": "array", "items": {"type": "string"}},
                            "translated_rules": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "source_path": {"type": "string"},
                                        "source_expression": {"type": "string"},
                                        "target_expression": {"type": "string"},
                                        "rule_type": {"type": "string"}
                                    },
                                    "required": ["source_path", "source_expression", "target_expression", "rule_type"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["target_sql", "assumptions", "potential_risks", "translated_rules"],
                        "additionalProperties": False
                    }
                }
            }
        else:
            body["response_format"] = {"type": "json_object"}

        max_retries = settings.LLM_MAX_RETRIES
        retry_delay = 2.0  # start with 2 seconds
        global_timeout_sec = 60.0

        for attempt in range(1, max_retries + 1):
            if (time.perf_counter() - start_time) > global_timeout_sec:
                raise ProviderExecutionTimeoutError("Global execution timeout exceeded during LLM retries.")

            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=settings.LLM_TIMEOUT_SECONDS) as res:
                    resp_data = json.loads(res.read().decode("utf-8"))
                    raw_text = resp_data["choices"][0]["message"]["content"] or ""
                    raw_json = _clean_json_response(raw_text)
                    usage_data = resp_data.get("usage", {})
                    input_tokens = usage_data.get("prompt_tokens", 0)
                    output_tokens = usage_data.get("completion_tokens", 0)
                    total_tokens = usage_data.get("total_tokens", 0)
                    provider_attempts = attempt
                    break  # Success, exit retry loop
            except urllib.error.HTTPError as http_err:
                if http_err.code in (401, 403):
                    raise NonRetryableProviderError(f"LLM_AUTH_ERROR: HTTP {http_err.code} Authentication Failed") from http_err
                
                elif http_err.code == 400:
                    error_body = ""
                    try:
                        error_body = http_err.read().decode("utf-8")
                        error_resp = json.loads(error_body)
                        error_type = error_resp.get("error", {}).get("type", "")
                        if "json_validate_failed" in error_type:
                            raise NonRetryableProviderError("json_validate_failed: Schema mismatch") from http_err
                    except Exception:
                        pass
                    raise NonRetryableProviderError(f"HTTP 400 Bad Request: {http_err.reason} - {error_body}") from http_err
                    
                elif http_err.code == 429:
                    error_body = ""
                    try:
                        error_body = http_err.read().decode("utf-8")
                        error_resp = json.loads(error_body)
                        err_obj = error_resp.get("error", {})
                        
                        err_type = err_obj.get("type", "")
                        err_code = err_obj.get("code", "")
                        err_message = err_obj.get("message", "").lower()
                        
                        is_exhaustion = False
                        if err_type == "tokens" and "rate_limit_exceeded" in err_code:
                            if "tokens per day" in err_message or "tpd" in err_message or "quota" in err_message:
                                is_exhaustion = True
                        elif "exhausted" in err_message or "limit_exceeded" in err_message or "credits" in err_message:
                            is_exhaustion = True
                            
                        if is_exhaustion:
                            retry_after_str = http_err.headers.get("retry-after", "0")
                            r_after = float(retry_after_str) if retry_after_str.replace(".", "").isdigit() else 0.0
                            raise ProviderTokenExhaustionError(
                                "LLM provider daily token limit exhausted.",
                                retry_after=r_after
                            )
                    except ProviderTokenExhaustionError:
                        raise
                    except Exception:
                        pass
                        
                    if attempt >= max_retries:
                        raise RateLimitError("HTTP 429 Rate Limit Exceeded (Max Retries Reached)") from http_err
                        
                    retry_after = http_err.headers.get("retry-after")
                    if retry_after and retry_after.replace(".", "").isdigit():
                        delay = float(retry_after)
                    else:
                        delay = retry_delay
                        
                    time.sleep(delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                    
                else:
                    if attempt >= max_retries:
                        raise TransientProviderError(f"LLM_PROVIDER_ERROR: HTTP {http_err.code}") from http_err
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
            except Exception as exc:
                if attempt >= max_retries:
                    raise TransientProviderError(f"LLM_PROVIDER_ERROR: {exc}") from exc
                time.sleep(retry_delay)
                retry_delay *= 2
                continue

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return RawProviderResponse(
            raw_json=raw_json,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            duration_ms=duration_ms,
            provider_attempts=provider_attempts,
        )


def get_llm_provider(
    provider_name: str | None = None,
    mock_mode: str | None = None,
) -> LLMProvider:
    """Factory function returning the configured LLMProvider instance."""
    if mock_mode:
        mode_str = mock_mode if mock_mode.startswith("MOCK_") else f"MOCK_{mock_mode.upper()}"
        return MockLLMProvider(mode=mode_str)

    p_name = (provider_name or settings.LLM_PROVIDER).lower()

    if p_name == "mock":
        return MockLLMProvider(mode="MOCK_GOOD")

    if p_name in ("openai", "openrouter", "groq"):
        settings.validate_llm_config()
        return OpenAIProvider()

    raise ValueError(f"Unsupported LLM provider: '{p_name}'. Allowed: 'openai', 'openrouter', 'groq', 'mock'.")
