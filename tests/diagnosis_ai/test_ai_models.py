"""Unit tests for Phase 7 Pydantic domain models."""

from backend.diagnosis_ai.models import (
    AIDiagnosis,
    DiagnosisStatus,
    EvidenceItem,
    EvidencePack,
    GroundedClaim,
    RepairChange,
    RepairProposal,
    RepairStatus,
)


def test_grounded_claim_model():
    claim = GroundedClaim(
        text="The target changed the comparison from strict to inclusive.",
        evidence_refs=["E-001", "E-002"],
    )
    assert claim.text == "The target changed the comparison from strict to inclusive."
    assert claim.evidence_refs == ["E-001", "E-002"]


def test_evidence_pack_model():
    item1 = EvidenceItem(
        evidence_id="E-001",
        evidence_type="SOURCE_EXPRESSION",
        description="Source SQL expression: t.amount > 500",
    )
    pack = EvidencePack(
        discrepancy_id="D-001",
        category="BOUNDARY_CONDITION",
        severity="HIGH",
        affected_row_count=10512,
        items=[item1],
    )
    assert pack.discrepancy_id == "D-001"
    assert len(pack.items) == 1
    assert pack.items[0].evidence_id == "E-001"


def test_ai_diagnosis_model():
    claim = GroundedClaim(text="Observed operator change", evidence_refs=["E-001"])
    diag = AIDiagnosis(
        diagnosis_id="diag-1",
        discrepancy_id="D-001",
        status=DiagnosisStatus.DIAGNOSED,
        observed_change="> became >=",
        likely_mechanism="Inclusive comparison",
        possible_cause="Translation operator mapping error",
        uncertainty="Evidence establishes operator shift",
        claims=[claim],
        diagnosis_confidence=0.98,
    )
    assert diag.status == DiagnosisStatus.DIAGNOSED
    assert diag.diagnosis_confidence == 0.98
    assert len(diag.claims) == 1


def test_repair_proposal_model():
    claim = GroundedClaim(text="Proposed repair restores threshold", evidence_refs=["E-001"])
    chg = RepairChange(
        location="columns[risk_class]",
        before_expression="t.amount >= 500",
        after_expression="t.amount > 500",
    )
    rep = RepairProposal(
        repair_id="rep-1",
        discrepancy_id="D-001",
        status=RepairStatus.PROPOSED,
        original_sql="SELECT * FROM t WHERE amount >= 500;",
        proposed_sql="SELECT * FROM t WHERE amount > 500;",
        changed_region="columns[risk_class]",
        changes=[chg],
        rationale="Restores strict comparison",
        expected_effect="Fixes boundary shift",
        claims=[claim],
        constraints_checked=["read_only_policy_enforced"],
        repair_confidence=0.96,
    )
    assert rep.status == RepairStatus.PROPOSED
    assert rep.repair_confidence == 0.96
    assert len(rep.changes) == 1
