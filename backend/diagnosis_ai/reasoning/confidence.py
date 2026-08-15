"""Confidence score calculation for Phase 7 AI Diagnosis and Repair Engine."""

from __future__ import annotations

from backend.diagnosis_ai.models import EvidencePack


def compute_diagnosis_confidence(evidence_pack: EvidencePack) -> float:
    """Calculate rule-based transparent diagnosis_confidence from EvidencePack profile."""
    score = 0.50
    item_types = {item.evidence_type for item in evidence_pack.items}

    if "SOURCE_EXPRESSION" in item_types:
        score += 0.15
    if "TARGET_EXPRESSION" in item_types:
        score += 0.15
    if "DISCREPANCY_IMPACT" in item_types and evidence_pack.affected_row_count > 0:
        score += 0.10
    if "REPRESENTATIVE_EXAMPLE" in item_types:
        score += 0.08

    return min(round(score, 2), 0.98)


def compute_repair_confidence(
    diagnosis_confidence: float,
    scope_valid: bool,
    contract_valid: bool,
    is_minimal: bool = True,
) -> float:
    """Calculate separate repair_confidence.

    Note: A strong diagnosis_confidence does not automatically imply a high repair_confidence.
    """
    if not scope_valid or not contract_valid:
        return 0.0

    score = diagnosis_confidence * 0.95
    if is_minimal:
        score += 0.02

    return min(round(score, 2), 0.96)
