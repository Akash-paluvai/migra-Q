"""Unit tests for DiagnosisContext and EvidencePack context builder."""

from backend.diagnosis_ai.context_builder import build_diagnosis_context, build_evidence_pack


def test_build_evidence_pack_stable_ids():
    pack = build_evidence_pack(
        discrepancy_id="D-001",
        category="BOUNDARY_CONDITION",
        severity="HIGH",
        source_expression="t.amount > 500",
        target_expression="t.amount >= 500",
        analysis_path="columns[risk_class]",
        affected_row_count=10512,
        affected_percentage=10.51,
        affected_columns=["risk_class"],
        representative_examples=[{"customer_id": "C18291", "refund": 500.0}],
        structural_differences=["ORDER BY clause added"],
    )

    ids = [item.evidence_id for item in pack.items]
    assert "E-001" in ids
    assert "E-002" in ids
    assert "E-003" in ids
    assert "E-004" in ids
    assert "E-005" in ids
    assert pack.affected_row_count == 10512


def test_build_diagnosis_context_hash_determinism():
    pack = build_evidence_pack(
        discrepancy_id="D-001",
        category="BOUNDARY_CONDITION",
        severity="HIGH",
        source_expression="t.amount > 500",
        target_expression="t.amount >= 500",
    )

    ctx1 = build_diagnosis_context(
        discrepancy_id="D-001",
        validation_id="val-1",
        translation_id="trans-1",
        source_sql="SELECT * FROM t WHERE amount > 500;",
        target_sql="SELECT * FROM t WHERE amount >= 500;",
        source_dialect="teradata",
        target_dialect="bigquery",
        evidence_pack=pack,
    )

    ctx2 = build_diagnosis_context(
        discrepancy_id="D-001",
        validation_id="val-1",
        translation_id="trans-1",
        source_sql="SELECT * FROM t WHERE amount > 500;",
        target_sql="SELECT * FROM t WHERE amount >= 500;",
        source_dialect="teradata",
        target_dialect="bigquery",
        evidence_pack=pack,
    )

    assert ctx1.context_hash == ctx2.context_hash
    assert len(ctx1.context_hash) == 64
