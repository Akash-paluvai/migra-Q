"""Tests for Phase 9 assurance scorer — SKIPPED → NOT_APPLICABLE exclusion."""

import pytest

from backend.assurance.models import AssuranceBand, ComponentStatus
from backend.assurance.scoring import AssuranceScorer
from backend.validation.models import (
    ValidationCheckStatus,
    ValidationReport,
    ValidationResult,
    ValidationSeverity,
)


@pytest.fixture
def scorer():
    return AssuranceScorer()


def _make_report(checks: list[tuple[str, ValidationCheckStatus, float]]) -> ValidationReport:
    """Build a ValidationReport from (check_name, status, score) triples."""
    results = [
        ValidationResult(
            check_name=name,
            status=status,
            score=score,
            severity=ValidationSeverity.HIGH,
            summary=f"{name} summary",
        )
        for name, status, score in checks
    ]
    return ValidationReport(
        validation_id="VAL-TEST",
        source_execution_id="EXEC-SRC",
        target_execution_id="EXEC-TGT",
        checks=results,
    )


class TestPerfectScore:
    def test_all_pass_score_100(self, scorer):
        report = _make_report([
            ("SchemaValidator", ValidationCheckStatus.PASS, 1.0),
            ("RowValidator", ValidationCheckStatus.PASS, 1.0),
            ("AggregateValidator", ValidationCheckStatus.PASS, 1.0),
            ("BusinessRuleValidator", ValidationCheckStatus.PASS, 1.0),
            ("EdgeCaseValidator", ValidationCheckStatus.PASS, 1.0),
        ])
        result = scorer.calculate(report)
        assert result.evidence_score == 100.0
        assert result.evidence_coverage == 100.0
        assert result.band == AssuranceBand.STRONG_EVIDENCE


class TestSkippedExclusion:
    def test_skipped_validator_excluded_from_denominator(self, scorer):
        """BusinessRuleValidator SKIPPED → NOT_APPLICABLE, excluded from score."""
        report = _make_report([
            ("SchemaValidator", ValidationCheckStatus.PASS, 1.0),
            ("RowValidator", ValidationCheckStatus.PASS, 1.0),
            ("AggregateValidator", ValidationCheckStatus.PASS, 1.0),
            ("BusinessRuleValidator", ValidationCheckStatus.SKIPPED, 0.0),
            ("EdgeCaseValidator", ValidationCheckStatus.PASS, 1.0),
        ])
        result = scorer.calculate(report)
        # Score should be 100 because all applicable components scored 100
        assert result.evidence_score == 100.0
        # Coverage should be 75% (0.10 + 0.30 + 0.20 + 0.15 = 0.75)
        assert result.evidence_coverage == 75.0

        # BusinessRuleValidator should be NOT_APPLICABLE
        biz = next(c for c in result.components if c.source_check == "BusinessRuleValidator")
        assert biz.status == ComponentStatus.NOT_APPLICABLE
        assert biz.effective_weight == 0.0
        assert biz.weighted_score == 0.0

    def test_skipped_never_interpreted_as_pass(self, scorer):
        """SKIPPED must not contribute to score, even with score=1.0."""
        report = _make_report([
            ("SchemaValidator", ValidationCheckStatus.PASS, 1.0),
            ("RowValidator", ValidationCheckStatus.PASS, 1.0),
            ("AggregateValidator", ValidationCheckStatus.SKIPPED, 1.0),
            ("BusinessRuleValidator", ValidationCheckStatus.SKIPPED, 1.0),
            ("EdgeCaseValidator", ValidationCheckStatus.PASS, 1.0),
        ])
        result = scorer.calculate(report)
        assert result.evidence_coverage == 55.0  # 10 + 30 + 15

        for c in result.components:
            if c.status == ComponentStatus.NOT_APPLICABLE:
                assert c.weighted_score == 0.0


class TestWeightRenormalization:
    def test_effective_weights_sum_to_one(self, scorer):
        """Effective weights of applicable components should sum to 1.0."""
        report = _make_report([
            ("SchemaValidator", ValidationCheckStatus.PASS, 1.0),
            ("RowValidator", ValidationCheckStatus.PASS, 1.0),
            ("AggregateValidator", ValidationCheckStatus.PASS, 1.0),
            ("BusinessRuleValidator", ValidationCheckStatus.SKIPPED, 0.0),
            ("EdgeCaseValidator", ValidationCheckStatus.PASS, 1.0),
        ])
        result = scorer.calculate(report)
        applicable = [c for c in result.components if c.status == ComponentStatus.SCORED]
        total = sum(c.effective_weight for c in applicable)
        assert abs(total - 1.0) < 1e-9

    def test_effective_weight_schema_renormalized(self, scorer):
        """Schema weight 0.10 → 0.10/0.75 ≈ 0.1333 when BusinessRule is skipped."""
        report = _make_report([
            ("SchemaValidator", ValidationCheckStatus.PASS, 1.0),
            ("RowValidator", ValidationCheckStatus.PASS, 1.0),
            ("AggregateValidator", ValidationCheckStatus.PASS, 1.0),
            ("BusinessRuleValidator", ValidationCheckStatus.SKIPPED, 0.0),
            ("EdgeCaseValidator", ValidationCheckStatus.PASS, 1.0),
        ])
        result = scorer.calculate(report)
        schema = next(c for c in result.components if c.source_check == "SchemaValidator")
        assert abs(schema.effective_weight - 0.10 / 0.75) < 1e-6


class TestReducedScores:
    def test_partial_failure_reduces_score(self, scorer):
        report = _make_report([
            ("SchemaValidator", ValidationCheckStatus.PASS, 1.0),
            ("RowValidator", ValidationCheckStatus.FAIL, 0.5),
            ("AggregateValidator", ValidationCheckStatus.PASS, 1.0),
            ("BusinessRuleValidator", ValidationCheckStatus.PASS, 1.0),
            ("EdgeCaseValidator", ValidationCheckStatus.PASS, 1.0),
        ])
        result = scorer.calculate(report)
        assert result.evidence_score < 100.0
        assert result.evidence_coverage == 100.0

    def test_error_gives_zero_score(self, scorer):
        report = _make_report([
            ("SchemaValidator", ValidationCheckStatus.PASS, 1.0),
            ("RowValidator", ValidationCheckStatus.ERROR, 0.0),
            ("AggregateValidator", ValidationCheckStatus.PASS, 1.0),
            ("BusinessRuleValidator", ValidationCheckStatus.PASS, 1.0),
            ("EdgeCaseValidator", ValidationCheckStatus.PASS, 1.0),
        ])
        result = scorer.calculate(report)
        row = next(c for c in result.components if c.source_check == "RowValidator")
        assert row.status == ComponentStatus.ERROR
        assert row.raw_score == 0.0


class TestBandClassification:
    def test_strong_evidence(self, scorer):
        report = _make_report([
            ("SchemaValidator", ValidationCheckStatus.PASS, 1.0),
            ("RowValidator", ValidationCheckStatus.PASS, 1.0),
            ("AggregateValidator", ValidationCheckStatus.PASS, 1.0),
            ("BusinessRuleValidator", ValidationCheckStatus.PASS, 1.0),
            ("EdgeCaseValidator", ValidationCheckStatus.PASS, 1.0),
        ])
        result = scorer.calculate(report)
        assert result.band == AssuranceBand.STRONG_EVIDENCE

    def test_poor_assurance_below_70(self, scorer):
        report = _make_report([
            ("SchemaValidator", ValidationCheckStatus.PASS, 1.0),
            ("RowValidator", ValidationCheckStatus.FAIL, 0.3),
            ("AggregateValidator", ValidationCheckStatus.FAIL, 0.2),
            ("BusinessRuleValidator", ValidationCheckStatus.FAIL, 0.1),
            ("EdgeCaseValidator", ValidationCheckStatus.FAIL, 0.1),
        ])
        result = scorer.calculate(report)
        assert result.band == AssuranceBand.POOR_ASSURANCE


class TestReproducibility:
    def test_same_input_same_output(self, scorer):
        report = _make_report([
            ("SchemaValidator", ValidationCheckStatus.PASS, 1.0),
            ("RowValidator", ValidationCheckStatus.PASS, 0.95),
            ("AggregateValidator", ValidationCheckStatus.PASS, 1.0),
            ("BusinessRuleValidator", ValidationCheckStatus.SKIPPED, 0.0),
            ("EdgeCaseValidator", ValidationCheckStatus.PASS, 1.0),
        ])
        r1 = scorer.calculate(report)
        r2 = scorer.calculate(report)
        assert r1.evidence_score == r2.evidence_score
        assert r1.evidence_coverage == r2.evidence_coverage
        assert r1.band == r2.band
