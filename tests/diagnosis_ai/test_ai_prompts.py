"""Unit tests for Phase 7 System Prompt and User Prompt formatting."""

from backend.diagnosis_ai.context_builder import build_diagnosis_context, build_evidence_pack
from backend.diagnosis_ai.prompts import (
    SYSTEM_PROMPT,
    build_diagnosis_user_prompt,
    compute_prompt_hash,
)


def test_system_prompt_directives():
    assert "EVIDENCE GROUNDING" in SYSTEM_PROMPT
    assert "SEPARATE MECHANISM FROM CAUSE" in SYSTEM_PROMPT
    assert "MINIMAL CANDIDATE REPAIR" in SYSTEM_PROMPT
    assert "READ-ONLY CANDIDATE" in SYSTEM_PROMPT
    assert "SECURITY ISOLATION" in SYSTEM_PROMPT


def test_build_diagnosis_user_prompt():
    pack = build_evidence_pack(
        discrepancy_id="D-001",
        category="BOUNDARY_CONDITION",
        severity="HIGH",
        source_expression="t.amount > 500",
        target_expression="t.amount >= 500",
    )
    ctx = build_diagnosis_context(
        discrepancy_id="D-001",
        validation_id="val-1",
        translation_id="trans-1",
        source_sql="SELECT * FROM t WHERE amount > 500;",
        target_sql="SELECT * FROM t WHERE amount >= 500;",
        source_dialect="teradata",
        target_dialect="bigquery",
        evidence_pack=pack,
    )

    user_prompt = build_diagnosis_user_prompt(ctx)
    assert "D-001" in user_prompt
    assert "BOUNDARY_CONDITION" in user_prompt
    assert "teradata" in user_prompt
    assert "bigquery" in user_prompt


def test_prompt_hash_determinism():
    h1 = compute_prompt_hash(SYSTEM_PROMPT, "user_prompt_text_1")
    h2 = compute_prompt_hash(SYSTEM_PROMPT, "user_prompt_text_1")
    h3 = compute_prompt_hash(SYSTEM_PROMPT, "user_prompt_text_2")

    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64
