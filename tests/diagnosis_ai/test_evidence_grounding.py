"""Unit tests verifying EvidenceGroundingValidator behavior."""

from backend.diagnosis_ai.context_builder import build_evidence_pack
from backend.diagnosis_ai.evidence import EvidenceGroundingValidator
from backend.diagnosis_ai.models import GroundedClaim


def test_valid_evidence_grounding_passes():
    pack = build_evidence_pack(
        discrepancy_id="D-001",
        category="BOUNDARY_CONDITION",
        severity="HIGH",
        source_expression="t.amount > 500",
        target_expression="t.amount >= 500",
        affected_row_count=10512,
    )

    diag_claims = [
        GroundedClaim(text="Source expression is t.amount > 500", evidence_refs=["E-001"]),
        GroundedClaim(text="Target expression is t.amount >= 500", evidence_refs=["E-002"]),
    ]
    rep_claims = [
        GroundedClaim(text="Affects 10,512 rows", evidence_refs=["E-003"]),
    ]

    valid, msg = EvidenceGroundingValidator.validate_grounding(diag_claims, rep_claims, pack)
    assert valid is True
    assert "successfully grounded" in msg


def test_unknown_evidence_ref_rejected():
    pack = build_evidence_pack(
        discrepancy_id="D-001",
        category="BOUNDARY_CONDITION",
        severity="HIGH",
        source_expression="t.amount > 500",
        target_expression="t.amount >= 500",
    )

    diag_claims = [
        GroundedClaim(text="Unknown evidence ref assertion", evidence_refs=["E-999"]),
    ]

    valid, msg = EvidenceGroundingValidator.validate_grounding(diag_claims, [], pack)
    assert valid is False
    assert "references unknown evidence ID 'E-999'" in msg


def test_empty_evidence_refs_rejected():
    pack = build_evidence_pack(
        discrepancy_id="D-001",
        category="BOUNDARY_CONDITION",
        severity="HIGH",
        source_expression="t.amount > 500",
    )

    diag_claims = [
        GroundedClaim(text="Claim with no refs", evidence_refs=[]),
    ]

    valid, msg = EvidenceGroundingValidator.validate_grounding(diag_claims, [], pack)
    assert valid is False
    assert "contains no evidence references" in msg
