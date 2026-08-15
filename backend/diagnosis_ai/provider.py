"""Provider abstraction and mock implementation for Phase 7 AI Diagnosis Engine.

Reuses Phase 6 provider gateway infrastructure for OpenAI transport and token tracking.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

from backend.core.config import settings
from backend.diagnosis_ai.models import (
    DiagnosisAIResponse,
    DiagnosisContext,
    GroundedClaim,
    RepairChange,
)
from backend.translator.provider import RawProviderResponse


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
    """Deterministic mock provider supporting 9 test scenarios."""

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

        elif self.mode == "MOCK_SCOPE_CREEP":
            # Modifies JOIN and GROUP BY when discrepancy is localized to risk_class
            creep_sql = """SELECT
  c.customer_id,
  c.customer_segment,
  SUM(t.amount) AS total_amount,
  CASE WHEN t.amount > 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t
LEFT JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id;"""
            resp = DiagnosisAIResponse(
                observed_change="Target comparison operator changed from > to >=.",
                likely_mechanism="Boundary comparison became inclusive.",
                possible_cause="Translation mapped comparison operator incorrectly.",
                uncertainty="Evidence directly establishes operator change.",
                diagnosis_claims=[
                    GroundedClaim(
                        text="Target changed comparison from strict to inclusive.",
                        evidence_refs=["E-001", "E-002"],
                    )
                ],
                proposed_sql=creep_sql,
                changed_region="columns[risk_class]",
                changes=[
                    RepairChange(
                        location="columns[risk_class]",
                        before_expression="t.amount >= 500",
                        after_expression="t.amount > 500",
                    )
                ],
                repair_rationale="Changed comparison operator but also modified JOIN and GROUP BY unnecessarily.",
                expected_effect="Restore strict threshold",
                repair_claims=[
                    GroundedClaim(
                        text="Proposed repair restores strict comparison.",
                        evidence_refs=["E-001", "E-003"],
                    )
                ],
            )

        elif self.mode == "MOCK_WRONG_DISCREPANCY_REPAIR":
            # Modifies SUM(t.amount) when discrepancy is localized to risk_class
            wrong_sql = """SELECT
  c.customer_id,
  c.customer_segment,
  COUNT(t.amount) AS total_amount,
  CASE WHEN t.amount >= 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;"""
            resp = DiagnosisAIResponse(
                observed_change="Target comparison operator changed from > to >=.",
                likely_mechanism="Boundary comparison became inclusive.",
                possible_cause="Translation mapped comparison operator incorrectly.",
                uncertainty="Evidence directly establishes operator change.",
                diagnosis_claims=[
                    GroundedClaim(
                        text="Target changed comparison from strict to inclusive.",
                        evidence_refs=["E-001", "E-002"],
                    )
                ],
                proposed_sql=wrong_sql,
                changed_region="columns[risk_class]",
                changes=[
                    RepairChange(
                        location="columns[total_amount]",
                        before_expression="SUM(t.amount)",
                        after_expression="COUNT(t.amount)",
                    )
                ],
                repair_rationale="Wrong repair modifying aggregation instead of risk_class.",
                expected_effect="None",
                repair_claims=[
                    GroundedClaim(
                        text="Modified aggregation column total_amount.",
                        evidence_refs=["E-003"],
                    )
                ],
            )

        elif self.mode == "MOCK_INVALID_TARGET":
            resp = DiagnosisAIResponse(
                observed_change="Target comparison operator changed.",
                likely_mechanism="Inclusive comparison.",
                possible_cause="Operator shift.",
                uncertainty="Uncertainty acknowledged.",
                diagnosis_claims=[
                    GroundedClaim(
                        text="Target comparison changed.",
                        evidence_refs=["E-001"],
                    )
                ],
                proposed_sql="INVALID SQL SELECT SYNTAX {{{",
                changed_region="columns[risk_class]",
                changes=[],
                repair_rationale="Malformed repair SQL",
                expected_effect="None",
                repair_claims=[
                    GroundedClaim(
                        text="Malformed SQL claim.",
                        evidence_refs=["E-001"],
                    )
                ],
            )

        else:  # MOCK_BOUNDARY_REPAIR and MOCK_CORRECT_DIAGNOSIS (Flagship Scenario)
            repaired_sql = """SELECT
  c.customer_id,
  c.customer_segment,
  SUM(t.amount) AS total_amount,
  CASE WHEN t.amount > 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;"""

            resp = DiagnosisAIResponse(
                observed_change="Target comparison operator changed from > to >=.",
                likely_mechanism="Boundary comparison became inclusive.",
                possible_cause="The translator may have mapped the comparison operator incorrectly.",
                uncertainty="Evidence directly establishes operator change and 10,512 row diff; it does not establish why the model selected >=.",
                diagnosis_claims=[
                    GroundedClaim(
                        text="The target comparison changed from strict (> 500) to inclusive (>= 500).",
                        evidence_refs=["E-001", "E-002"],
                    ),
                    GroundedClaim(
                        text="10,512 output rows are affected by this threshold shift.",
                        evidence_refs=["E-003"],
                    ),
                    GroundedClaim(
                        text="Representative row with amount=500.00 classified as NORMAL in source and HIGH_RISK in target.",
                        evidence_refs=["E-004"],
                    ),
                ],
                proposed_sql=repaired_sql,
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
    """OpenAI implementation using structured JSON output."""

    def __init__(self) -> None:
        if not settings.LLM_API_KEY:
            raise ValueError("LLM_API_KEY environment variable is not configured.")
        from openai import OpenAI

        self.client = OpenAI(api_key=settings.LLM_API_KEY)
        self.model_name = settings.LLM_MODEL or "gpt-4o"

    def generate_diagnosis_and_repair(
        self,
        system_prompt: str,
        user_prompt: str,
        context: DiagnosisContext,
    ) -> tuple[DiagnosisAIResponse, RawProviderResponse]:
        start_time = time.perf_counter()

        completion = self.client.beta.chat.completions.parse(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=DiagnosisAIResponse,
            temperature=settings.LLM_TEMPERATURE,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        parsed = completion.choices[0].message.parsed

        usage = completion.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0

        raw_resp = RawProviderResponse(
            raw_json=completion.choices[0].message.content or parsed.model_dump_json(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            duration_ms=duration_ms,
        )
        return parsed, raw_resp
