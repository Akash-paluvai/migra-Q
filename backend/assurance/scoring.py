"""Assurance scorer — honest scoring with SKIPPED → NOT_APPLICABLE exclusion.

SKIPPED must never be interpreted as PASS.
SKIPPED means: 'This validator did not evaluate this dimension.'

The score describes evidence. The gates determine the decision.
"""

from __future__ import annotations

from backend.assurance.models import (
    AssuranceBand,
    AssuranceScore,
    ComponentStatus,
    ScoreComponent,
)
from backend.validation.models import ValidationCheckStatus, ValidationReport

# Nominal weights for each validation component.
# When a component is NOT_APPLICABLE, its weight is excluded from the denominator.
COMPONENT_WEIGHTS: list[tuple[str, float, str]] = [
    ("Schema compatibility", 0.10, "SchemaValidator"),
    ("Row reconciliation", 0.30, "RowValidator"),
    ("Aggregate reconciliation", 0.20, "AggregateValidator"),
    ("Business-rule equivalence", 0.25, "BusinessRuleValidator"),
    ("Edge-case coverage", 0.15, "EdgeCaseValidator"),
]


def _classify_check_status(status: ValidationCheckStatus) -> ComponentStatus:
    """Map a Phase 4 validation check status to a scoring component status.

    - PASS / WARN / FAIL → SCORED (actual score is meaningful)
    - SKIPPED → NOT_APPLICABLE (excluded from denominator)
    - ERROR → ERROR (score is 0)
    """
    if status == ValidationCheckStatus.SKIPPED:
        return ComponentStatus.NOT_APPLICABLE
    if status == ValidationCheckStatus.ERROR:
        return ComponentStatus.ERROR
    return ComponentStatus.SCORED


def _score_to_band(score: float) -> AssuranceBand:
    """Map a numeric score to a descriptive assurance band."""
    if score >= 95.0:
        return AssuranceBand.STRONG_EVIDENCE
    if score >= 85.0:
        return AssuranceBand.MINOR_CONCERNS
    if score >= 70.0:
        return AssuranceBand.SIGNIFICANT_CONCERNS
    return AssuranceBand.POOR_ASSURANCE


class AssuranceScorer:
    """Calculates assurance score with honest coverage tracking.

    Only SCORED components contribute to the evidence score.
    NOT_APPLICABLE components are excluded from the denominator.
    ERROR components contribute 0 to the score.

    Output:
      - evidence_score: weighted sum over applicable components [0, 100]
      - evidence_coverage: applicable_weight_sum as percentage [0, 100]
    """

    def calculate(self, validation_report: ValidationReport | None) -> AssuranceScore:
        """Calculate assurance score from Phase 4 validation report.

        Args:
            validation_report: Complete Phase 4 validation report, or None if validation did not run.

        Returns:
            AssuranceScore with evidence_score, evidence_coverage, components, and band.
        """
        if validation_report is None or not getattr(validation_report, "checks", None):
            return AssuranceScore(
                evidence_score=None,
                evidence_coverage=None,
                band=None,
                components=[],
            )

        # Build a lookup of check_name -> (status, score)
        check_lookup: dict[str, tuple[ValidationCheckStatus, float]] = {}
        for check in validation_report.checks:
            check_lookup[check.check_name] = (check.status, check.score)

        components: list[ScoreComponent] = []
        for name, weight, source_check in COMPONENT_WEIGHTS:
            if source_check in check_lookup:
                status_enum, raw_score = check_lookup[source_check]
                comp_status = _classify_check_status(status_enum)
                # Normalize score to [0, 100] scale (Phase 4 scores are [0.0, 1.0])
                raw_100 = raw_score * 100.0
                if comp_status == ComponentStatus.ERROR:
                    raw_100 = 0.0
            else:
                # Check not present in report — treat as NOT_APPLICABLE
                comp_status = ComponentStatus.NOT_APPLICABLE
                raw_100 = 0.0

            components.append(ScoreComponent(
                name=name,
                weight=weight,
                raw_score=raw_100,
                weighted_score=0.0,  # computed below
                effective_weight=0.0,  # computed below
                status=comp_status,
                source_check=source_check,
            ))

        # Calculate applicable weight sum (only SCORED and ERROR components)
        applicable_weight_sum = sum(
            c.weight for c in components if c.status in (ComponentStatus.SCORED, ComponentStatus.ERROR)
        )

        # Evidence coverage: percentage of total weight that was actually evaluated
        evidence_coverage = applicable_weight_sum * 100.0  # total nominal weight is 1.0

        # Calculate effective weights and weighted scores
        evidence_score = 0.0
        if applicable_weight_sum > 0:
            for c in components:
                if c.status in (ComponentStatus.SCORED, ComponentStatus.ERROR):
                    c.effective_weight = c.weight / applicable_weight_sum
                    c.weighted_score = c.raw_score * c.effective_weight
                    evidence_score += c.weighted_score
                else:
                    c.effective_weight = 0.0
                    c.weighted_score = 0.0

        band = _score_to_band(evidence_score)

        return AssuranceScore(
            evidence_score=round(evidence_score, 2),
            evidence_coverage=round(evidence_coverage, 1),
            band=band,
            components=components,
        )
