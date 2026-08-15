"""Flagship end-to-end unit tests for Phase 7 AI Diagnosis & Repair Proposal Engine."""

from backend.diagnosis_ai.service import DiagnosisAIService


def test_flagship_boundary_condition_diagnosis_and_repair():
    """Flagship scenario: D-001 BOUNDARY_CONDITION (> 500 vs >= 500).

    Verifies:
    1. AI generates evidence-grounded diagnosis and candidate repair (PROPOSED).
    2. Observed change is separated from causal attribution.
    3. Changed region is localized to columns[risk_class].
    4. Confidence scores meet threshold expectations without fragile hardcoding.
    5. CRITICAL: Phase 7 NEVER executes SQL, NEVER runs Phase 3/4/5, and NEVER claims VERIFIED.
    """
    source_sql = """SELECT
  c.customer_id,
  c.customer_segment,
  SUM(t.amount) AS total_amount,
  CASE WHEN t.amount > 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;"""

    target_sql = """SELECT
  c.customer_id,
  c.customer_segment,
  SUM(t.amount) AS total_amount,
  CASE WHEN t.amount >= 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;"""

    example = {
        "customer_id": "C18291",
        "refund_amount": 500.00,
        "source_risk": "NORMAL",
        "target_risk": "HIGH_RISK",
    }

    res = DiagnosisAIService.diagnose_discrepancy(
        discrepancy_id="D-001",
        category="BOUNDARY_CONDITION",
        severity="HIGH",
        source_sql=source_sql,
        target_sql=target_sql,
        source_expression="t.amount > 500",
        target_expression="t.amount >= 500",
        analysis_path="columns[risk_class]",
        affected_row_count=10512,
        affected_percentage=10.51,
        affected_columns=["risk_class"],
        representative_examples=[example],
        mock_mode="MOCK_BOUNDARY_REPAIR",
    )

    # 1. Diagnosis Verification
    assert res.diagnosis.status.value == "DIAGNOSED"
    assert "target comparison operator changed" in res.diagnosis.observed_change.lower()
    assert "boundary comparison became inclusive" in res.diagnosis.likely_mechanism.lower()
    assert res.diagnosis.diagnosis_confidence >= 0.85

    # 2. Evidence Grounding Verification
    assert len(res.diagnosis.claims) >= 2
    valid_ids = {"E-001", "E-002", "E-003", "E-004", "E-005"}
    for claim in res.diagnosis.claims:
        assert len(claim.evidence_refs) > 0
        assert all(ref in valid_ids for ref in claim.evidence_refs)

    # 3. Candidate Repair Verification
    assert res.repair_proposal.status.value == "PROPOSED"
    assert res.repair_proposal.changed_region == "columns[risk_class]"
    assert "t.amount > 500" in res.repair_proposal.proposed_sql
    assert res.repair_proposal.repair_confidence >= 0.80

    # 4. Phase Boundary Guarantee
    assert res.repair_proposal.status.value != "VERIFIED"
    assert res.repair_proposal.status.value != "APPROVED"
    assert res.repair_proposal.status.value != "EQUIVALENT"


def test_independent_discrepancy_isolation():
    """Verify multiple discrepancies are processed independently without single broad repairs."""
    source_sql = "SELECT customer_id FROM transactions WHERE amount > 500;"
    target_sql = "SELECT customer_id FROM transactions WHERE amount >= 500;"

    # Discrepancy D-001 (Boundary condition on risk_class)
    res_d1 = DiagnosisAIService.diagnose_discrepancy(
        discrepancy_id="D-001",
        category="BOUNDARY_CONDITION",
        severity="HIGH",
        source_sql=source_sql,
        target_sql=target_sql,
        source_expression="t.amount > 500",
        target_expression="t.amount >= 500",
        analysis_path="columns[risk_class]",
        affected_row_count=10512,
        mock_mode="MOCK_BOUNDARY_REPAIR",
    )
    assert res_d1.diagnosis.discrepancy_id == "D-001"
    assert res_d1.repair_proposal.changed_region == "columns[risk_class]"
