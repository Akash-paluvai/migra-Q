"""Repair proposal helper module for Phase 7."""

from __future__ import annotations

from backend.diagnosis_ai.models import GroundedClaim, RepairChange, RepairProposal, RepairStatus


def format_repair_proposal(
    repair_id: str,
    discrepancy_id: str,
    status: RepairStatus,
    original_sql: str,
    proposed_sql: str,
    changed_region: str,
    changes: list[RepairChange],
    rationale: str,
    expected_effect: str,
    claims: list[GroundedClaim],
    constraints_checked: list[str],
    repair_confidence: float,
) -> RepairProposal:
    """Construct structured RepairProposal domain model."""
    return RepairProposal(
        repair_id=repair_id,
        discrepancy_id=discrepancy_id,
        status=status,
        original_sql=original_sql,
        proposed_sql=proposed_sql,
        changed_region=changed_region,
        changes=changes,
        rationale=rationale,
        expected_effect=expected_effect,
        claims=claims,
        constraints_checked=constraints_checked,
        repair_confidence=repair_confidence,
    )
