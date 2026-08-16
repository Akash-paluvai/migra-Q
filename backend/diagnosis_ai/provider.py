"""Provider abstraction and mock implementation for Phase 7 AI Diagnosis Engine.

Reuses Phase 6 provider gateway infrastructure for OpenAI / OpenRouter transport and token tracking.
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod

from backend.core.config import settings
from backend.diagnosis_ai.models import (
    DiagnosisAIResponse,
    DiagnosisContext,
    GroundedClaim,
    RepairChange,
)
from backend.translator.provider import RawProviderResponse, _clean_json_response


class AIDiagnosisProvider(ABC):
    """Abstract interface for AI diagnosis and repair proposal generation."""

    @abstractmethod
    def generate_diagnosis_and_repair(
        self,
        system_prompt: str,
        user_prompt: str,
        context: DiagnosisContext,
    ) -> tuple[DiagnosisAIResponse, RawProviderResponse]:
        """Generate structured DiagnosisAIResponse from prompts and context."""
        pass


class MockDiagnosisProvider(AIDiagnosisProvider):
    """Deterministic mock provider supporting test scenarios."""

    def __init__(self, mode: str = "MOCK_BOUNDARY_REPAIR") -> None:
        self.mode = mode

    def generate_diagnosis_and_repair(
        self,
        system_prompt: str,
        user_prompt: str,
        context: DiagnosisContext,
    ) -> tuple[DiagnosisAIResponse, RawProviderResponse]:
        start_time = time.perf_counter()

        if self.mode == "MOCK_NO_REPAIR":
            resp = DiagnosisAIResponse(
                observed_change="Unclear operator difference in target query.",
                likely_mechanism="Ambiguous filter semantics in source vs target.",
                possible_cause="Insufficient evidence to isolate exact boundary condition.",
                uncertainty="Evidence pack lacks sufficient row-level boundary examples.",
                diagnosis_claims=[
                    GroundedClaim(
                        text="Insufficient evidence to identify exact target expression.",
                        evidence_refs=["E-003"],
                    )
                ],
                proposed_sql=None,
                changed_region=None,
                changes=[],
                repair_rationale=None,
                expected_effect=None,
                repair_claims=[],
            )

        elif self.mode == "MOCK_UNGROUNDED_CLAIM":
            resp = DiagnosisAIResponse(
                observed_change="Target changed comparison operator.",
                likely_mechanism="Boundary condition shifted.",
                possible_cause="Translator misinterpretation.",
                uncertainty="No evidence.",
                diagnosis_claims=[
                    GroundedClaim(
                        text="Target changed comparison operator without evidence refs.",
                        evidence_refs=[],
                    )
                ],
                proposed_sql=context.target_sql,
                changed_region="columns[risk_class]",
                changes=[],
                repair_rationale="Attempted repair",
                expected_effect="None",
                repair_claims=[],
            )

        elif self.mode == "MOCK_UNKNOWN_EVIDENCE_REF":
            resp = DiagnosisAIResponse(
                observed_change="Target comparison operator changed.",
                likely_mechanism="Inclusive comparison applied.",
                possible_cause="Operator translation error.",
                uncertainty="Uncertainty acknowledged.",
                diagnosis_claims=[
                    GroundedClaim(
                        text="Target threshold comparison changed.",
                        evidence_refs=["E-999"],
                    )
                ],
                proposed_sql=context.target_sql,
                changed_region="columns[risk_class]",
                changes=[],
                repair_rationale="Attempted repair",
                expected_effect="None",
                repair_claims=[],
            )

        elif self.mode == "MOCK_UNSAFE_DDL":
            resp = DiagnosisAIResponse(
                observed_change="Target query contains boundary error.",
                likely_mechanism="Inclusive predicate applied.",
                possible_cause="Translator introduced inclusive relational operator.",
                uncertainty="Uncertainty acknowledged.",
                diagnosis_claims=[
                    GroundedClaim(
                        text="Target query uses inclusive relational operator.",
                        evidence_refs=["E-001"],
                    )
                ],
                proposed_sql="DROP TABLE transactions;",
                changed_region="columns[risk_class]",
                changes=[],
                repair_rationale="Unsafe repair attempt",
                expected_effect="Mutates schema",
                repair_claims=[],
            )

        elif self.mode == "MOCK_SYNTAX_ERROR":
            resp = DiagnosisAIResponse(
                observed_change="Target query contains boundary error.",
                likely_mechanism="Inclusive predicate applied.",
                possible_cause="Translator introduced inclusive relational operator.",
                uncertainty="Uncertainty acknowledged.",
                diagnosis_claims=[
                    GroundedClaim(
                        text="Target query uses inclusive relational operator.",
                        evidence_refs=["E-001"],
                    )
                ],
                proposed_sql="SELECT INVALID SYNTAX FROM WHERE",
                changed_region="columns[risk_class]",
                changes=[],
                repair_rationale="Invalid syntax attempt",
                expected_effect="Fails syntax check",
                repair_claims=[],
            )

        elif self.mode == "MOCK_CONTRACT_BREAK":
            resp = DiagnosisAIResponse(
                observed_change="Target query contains boundary error.",
                likely_mechanism="Inclusive predicate applied.",
                possible_cause="Translator introduced inclusive relational operator.",
                uncertainty="Uncertainty acknowledged.",
                diagnosis_claims=[
                    GroundedClaim(
                        text="Target query uses inclusive relational operator.",
                        evidence_refs=["E-001"],
                    )
                ],
                proposed_sql="SELECT customer_id FROM transactions;",
                changed_region="columns[risk_class]",
                changes=[],
                repair_rationale="Alters output schema",
                expected_effect="Breaks contract",
                repair_claims=[],
            )

        elif self.mode == "MOCK_REPAIR_FAILS_VERIFICATION":
            resp = DiagnosisAIResponse(
                observed_change="Target query contains boundary error.",
                likely_mechanism="Inclusive predicate applied.",
                possible_cause="Translator introduced inclusive relational operator.",
                uncertainty="Uncertainty acknowledged.",
                diagnosis_claims=[
                    GroundedClaim(
                        text="Target query uses inclusive relational operator.",
                        evidence_refs=["E-001"],
                    )
                ],
                proposed_sql=context.target_sql.replace(">= 500", ">= 400"),
                changed_region="columns[risk_class]",
                changes=[
                    RepairChange(
                        location="columns[risk_class]",
                        before_expression="t.amount >= 500",
                        after_expression="t.amount >= 400",
                        change_type="MODIFY",
                    )
                ],
                repair_rationale="Incorrect repair predicate.",
                expected_effect="Fails verification.",
                repair_claims=[
                    GroundedClaim(
                        text="Attempted threshold adjustment.",
                        evidence_refs=["E-001"],
                    )
                ],
            )

        elif self.mode == "MOCK_SCOPE_CREEP":
            resp = DiagnosisAIResponse(
                observed_change="Target comparison operator changed and scope extended.",
                likely_mechanism="Inclusive predicate applied with extra join and group by changes.",
                possible_cause="Translator altered join and group by structure.",
                uncertainty="Uncertainty acknowledged.",
                diagnosis_claims=[
                    GroundedClaim(
                        text="Target query uses inclusive relational operator.",
                        evidence_refs=["E-001"],
                    )
                ],
                proposed_sql=context.target_sql.replace(">= 500", "> 500").replace("t.status = 'COMPLETED'", "t.status = 'COMPLETED' AND c.customer_segment != 'EXCLUDED'"),
                changed_region="columns[risk_class]",
                changes=[
                    RepairChange(
                        location="columns[risk_class]",
                        before_expression="t.amount >= 500",
                        after_expression="t.amount > 500",
                        change_type="MODIFY",
                    ),
                    RepairChange(
                        location="joins[0]",
                        before_expression="t.status = 'COMPLETED'",
                        after_expression="t.status = 'COMPLETED' AND c.customer_segment != 'EXCLUDED'",
                        change_type="MODIFY",
                    ),
                    RepairChange(
                        location="groupby",
                        before_expression="GROUP BY c.customer_id",
                        after_expression="GROUP BY c.customer_id, c.customer_segment",
                        change_type="MODIFY",
                    ),
                ],
                repair_rationale="Scope creep repair attempt.",
                expected_effect="Unjustified scope change.",
                repair_claims=[
                    GroundedClaim(
                        text="Attempted threshold and join adjustment.",
                        evidence_refs=["E-001"],
                    )
                ],
            )

        else:  # MOCK_BOUNDARY_REPAIR (Default valid candidate repair)
            resp = DiagnosisAIResponse(
                observed_change="Target comparison operator changed: target query uses inclusive operator (>= 500.00) instead of strict comparison (> 500).",
                likely_mechanism="Boundary comparison became inclusive: relational operator classifies boundary values ($500.00) as HIGH_RISK instead of NORMAL.",
                possible_cause="Translator LLM introduced inclusive relational operator during syntax generation.",
                uncertainty="Execution evidence proves behavioral difference with 100% certainty, but cannot establish prompt intent.",
                diagnosis_claims=[
                    GroundedClaim(
                        text="Target query uses inclusive relational operator (>= 500.00).",
                        evidence_refs=["E-001", "E-002"],
                    ),
                    GroundedClaim(
                        text="Execution evidence confirms boundary row discrepancy at threshold value 500.00.",
                        evidence_refs=["E-001"],
                    ),
                ],
                proposed_sql=context.target_sql.replace(">= 500", "> 500"),
                changed_region="columns[risk_class]",
                changes=[
                    RepairChange(
                        location="columns[risk_class]",
                        before_expression="t.amount >= 500",
                        after_expression="t.amount > 500",
                        change_type="MODIFY",
                    )
                ],
                repair_rationale="Restores strict comparison operator (> 500) in CASE statement predicate.",
                expected_effect="Restores strict boundary classification semantics for risk_class.",
                repair_claims=[
                    GroundedClaim(
                        text="Proposed candidate repair restores strict threshold comparison (> 500).",
                        evidence_refs=["E-001", "E-002"],
                    )
                ],
            )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        raw_provider_resp = RawProviderResponse(
            raw_json=resp.model_dump_json(),
            input_tokens=150,
            output_tokens=80,
            total_tokens=230,
            duration_ms=duration_ms,
        )
        return resp, raw_provider_resp


class OpenAIDiagnosisProvider(AIDiagnosisProvider):
    """OpenAI / OpenRouter provider for AI Diagnosis Engine using structured JSON output."""

    def __init__(self) -> None:
        self.api_key = settings.LLM_API_KEY
        self.model_name = settings.LLM_MODEL or "nvidia/nemotron-3-ultra-550b-a55b:free"
        self.base_url = settings.LLM_BASE_URL or "https://openrouter.ai/api/v1"

        if not self.api_key:
            raise ValueError("LLM_API_KEY environment variable is not configured.")

    def generate_diagnosis_and_repair(
        self,
        system_prompt: str,
        user_prompt: str,
        context: DiagnosisContext,
    ) -> tuple[DiagnosisAIResponse, RawProviderResponse]:
        """Call OpenRouter / OpenAI chat completions API via urllib for diagnosis."""
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
            "model": self.model_name,
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_OUTPUT_TOKENS,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        # Dynamic Response Format Selection
        if "gpt-oss" in self.model_name or "gpt-4" in self.model_name:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "diagnosis_response",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "observed_change": {"type": "string"},
                            "likely_mechanism": {"type": "string"},
                            "possible_cause": {"type": "string"},
                            "uncertainty": {"type": "string"},
                            "diagnosis_claims": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string"},
                                        "evidence_refs": {"type": "array", "items": {"type": "string"}}
                                    },
                                    "required": ["text", "evidence_refs"],
                                    "additionalProperties": False
                                }
                            },
                            "proposed_sql": {"type": ["string", "null"]},
                            "changed_region": {"type": ["string", "null"]},
                            "changes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "location": {"type": "string"},
                                        "before_expression": {"type": "string"},
                                        "after_expression": {"type": "string"},
                                        "change_type": {"type": "string"}
                                    },
                                    "required": ["location", "before_expression", "after_expression", "change_type"],
                                    "additionalProperties": False
                                }
                            },
                            "repair_rationale": {"type": ["string", "null"]},
                            "expected_effect": {"type": ["string", "null"]},
                            "repair_claims": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string"},
                                        "evidence_refs": {"type": "array", "items": {"type": "string"}}
                                    },
                                    "required": ["text", "evidence_refs"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": [
                            "observed_change", "likely_mechanism", "possible_cause", "uncertainty", 
                            "diagnosis_claims", "proposed_sql", "changed_region", "changes", 
                            "repair_rationale", "expected_effect", "repair_claims"
                        ],
                        "additionalProperties": False
                    }
                }
            }
        else:
            body["response_format"] = {"type": "json_object"}

        max_retries = settings.LLM_MAX_RETRIES
        retry_delay = 2.0  # start with 2 seconds

        for attempt in range(1, max_retries + 1):
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=settings.LLM_TIMEOUT_SECONDS) as res:
                    resp_data = json.loads(res.read().decode("utf-8"))
                    raw_json_str = resp_data["choices"][0]["message"]["content"] or ""
                    usage_data = resp_data.get("usage", {})
                    input_tokens = usage_data.get("prompt_tokens", 0)
                    output_tokens = usage_data.get("completion_tokens", 0)
                    total_tokens = usage_data.get("total_tokens", 0)
                    break  # Success, exit retry loop
            except urllib.error.HTTPError as http_err:
                if http_err.code == 429 and attempt < max_retries:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                raise RuntimeError(f"LLM_DIAGNOSIS_HTTP_ERROR: HTTP {http_err.code}") from http_err
            except Exception as exc:
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise RuntimeError(f"LLM_DIAGNOSIS_HTTP_ERROR: {exc}") from exc

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Clean raw JSON output (stripping markdown ```json ... ``` codeblocks)
        cleaned_json = _clean_json_response(raw_json_str)

        try:
            parsed = DiagnosisAIResponse.model_validate_json(cleaned_json)
        except Exception as parse_exc:
            raise RuntimeError(f"Failed to parse LLM diagnosis JSON: {parse_exc}. Raw text: {raw_json_str[:300]}") from parse_exc

        raw_resp = RawProviderResponse(
            raw_json=cleaned_json,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            duration_ms=duration_ms,
        )
        return parsed, raw_resp


# Alias for generic OpenAI-compatible API providers (OpenRouter, Groq, Ollama, etc.)
OpenAICompatibleDiagnosisProvider = OpenAIDiagnosisProvider
