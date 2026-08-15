"""Diagnosis structure helper module for Phase 7."""

from __future__ import annotations

from backend.diagnosis_ai.models import AIDiagnosis, DiagnosisStatus, GroundedClaim


def format_diagnosis_summary(
    diagnosis_id: str,
    discrepancy_id: str,
    status: DiagnosisStatus,
    observed_change: str,
    likely_mechanism: str,
    possible_cause: str,
    uncertainty: str,
    claims: list[GroundedClaim],
    diagnosis_confidence: float,
) -> AIDiagnosis:
    """Construct structured AIDiagnosis domain model."""
    return AIDiagnosis(
        diagnosis_id=diagnosis_id,
        discrepancy_id=discrepancy_id,
        status=status,
        observed_change=observed_change,
        likely_mechanism=likely_mechanism,
        possible_cause=possible_cause,
        uncertainty=uncertainty,
        claims=claims,
        diagnosis_confidence=diagnosis_confidence,
    )
