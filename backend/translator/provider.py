"""LLM Provider abstraction layer — defines interface, OpenAI provider, and Mock provider."""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from backend.core.config import settings
from backend.translator.models import TranslationContext


@dataclass
class RawProviderResponse:
    """Raw response output container from an LLM provider call."""

    raw_json: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    duration_ms: float = 0.0


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
            raise TimeoutError("LLM provider request timed out.")

        if self.mode == "MOCK_AUTH_ERROR":
            raise PermissionError("Authentication failed: invalid API key.")

        if self.mode == "MOCK_RATE_LIMIT":
            raise RuntimeError("Rate limit exceeded: 429 Too Many Requests.")

        if self.mode == "MOCK_INVALID_JSON":
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return RawProviderResponse(
                raw_json="INVALID_JSON_RAW_TEXT{{{",
                input_tokens=100,
                output_tokens=20,
                total_tokens=120,
                duration_ms=duration_ms,
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
            payload = {
                "target_sql": """SELECT
  c.customer_id,
  c.customer_segment,
  SUM(t.amount) AS total_amount,
  CASE WHEN t.amount > 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;""",
                "assumptions": ["Converted Teradata JOIN syntax to BigQuery standard SQL"],
                "potential_risks": ["Verify implicit type coercions"],
                "translated_rules": [
                    {
                        "source_path": "business_rules[0]",
                        "source_expression": "t.amount > 500",
                        "target_expression": "t.amount > 500",
                        "rule_type": "comparison",
                    }
                ],
            }

        raw_json = json.dumps(payload)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return RawProviderResponse(
            raw_json=raw_json,
            input_tokens=250,
            output_tokens=150,
            total_tokens=400,
            duration_ms=duration_ms,
        )


class OpenAIProvider(LLMProvider):
    """Production provider calling OpenAI API via official OpenAI SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ):
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        self.timeout = timeout or settings.LLM_TIMEOUT_SECONDS

        if not self.api_key:
            raise ValueError(
                "OpenAI API key must be provided or configured in settings.LLM_API_KEY."
            )
        if not self.model:
            raise ValueError(
                "OpenAI model name must be provided or configured in settings.LLM_MODEL."
            )

        try:
            import openai

            self.client = openai.OpenAI(api_key=self.api_key, timeout=self.timeout)
        except ImportError:
            raise ImportError("openai package is not installed. Install via `pip install openai`.")

    def generate_translation(
        self,
        context: TranslationContext,
        system_prompt: str,
        user_prompt: str,
    ) -> RawProviderResponse:
        """Call OpenAI chat completions endpoint requesting JSON object output."""
        import openai

        start_time = time.perf_counter()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except openai.AuthenticationError as e:
            raise PermissionError(f"LLM_AUTH_ERROR: {e}") from e
        except openai.RateLimitError as e:
            raise RuntimeError(f"LLM_RATE_LIMIT: {e}") from e
        except openai.APITimeoutError as e:
            raise TimeoutError(f"LLM_TIMEOUT: {e}") from e
        except openai.APIError as e:
            raise RuntimeError(f"LLM_PROVIDER_ERROR: {e}") from e
        except Exception as e:
            raise RuntimeError(f"LLM_PROVIDER_ERROR: {e}") from e

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        choice = response.choices[0]
        raw_json = choice.message.content or ""

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else None
        output_tokens = usage.completion_tokens if usage else None
        total_tokens = usage.total_tokens if usage else None

        return RawProviderResponse(
            raw_json=raw_json,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            duration_ms=duration_ms,
        )


def get_llm_provider(
    provider_name: str | None = None,
    mock_mode: str = "MOCK_GOOD",
) -> LLMProvider:
    """Factory function returning the configured LLMProvider instance."""
    p_name = (provider_name or settings.LLM_PROVIDER).lower()

    if p_name == "mock":
        return MockLLMProvider(mode=mock_mode)

    if p_name == "openai":
        settings.validate_llm_config()
        return OpenAIProvider()

    raise ValueError(f"Unsupported LLM provider: '{p_name}'. Allowed: 'openai', 'mock'.")
