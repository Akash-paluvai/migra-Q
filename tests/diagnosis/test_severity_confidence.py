"""Unit tests for SeverityCalculator and ConfidenceCalculator."""

from backend.diagnosis.confidence import ConfidenceCalculator
from backend.diagnosis.models import DiscrepancyCategory, DiscrepancySeverity
from backend.diagnosis.severity import SeverityCalculator


def test_severity_structural_only_zero_affected_rows():
    sev = SeverityCalculator.calculate_severity(
        category=DiscrepancyCategory.BOUNDARY_CONDITION,
        affected_row_count=0,
        total_output_rows=1000000,
    )
    assert sev == DiscrepancySeverity.LOW


def test_severity_localized_affected_rows():
    sev = SeverityCalculator.calculate_severity(
        category=DiscrepancyCategory.FILTER_LOGIC,
        affected_row_count=5,
        total_output_rows=1000000,
    )
    assert sev == DiscrepancySeverity.MEDIUM


def test_severity_high_population_affected():
    sev = SeverityCalculator.calculate_severity(
        category=DiscrepancyCategory.BOUNDARY_CONDITION,
        affected_row_count=229,
        total_output_rows=1000,
    )
    assert sev in (DiscrepancySeverity.HIGH, DiscrepancySeverity.CRITICAL)


def test_severity_critical_cardinality_shift():
    sev = SeverityCalculator.calculate_severity(
        category=DiscrepancyCategory.JOIN_SEMANTICS,
        affected_row_count=30000,
        total_output_rows=100000,
    )
    assert sev == DiscrepancySeverity.CRITICAL


def test_confidence_structural_only():
    # Structural rule match only -> 0.85
    conf = ConfidenceCalculator.calculate_confidence(
        has_structural_match=True,
        has_execution_evidence=False,
        has_edge_case_confirmation=False,
    )
    assert conf == 0.85


def test_confidence_structural_and_execution():
    # Structural + execution evidence -> 0.95
    conf = ConfidenceCalculator.calculate_confidence(
        has_structural_match=True,
        has_execution_evidence=True,
        has_edge_case_confirmation=False,
    )
    assert conf == 0.95


def test_confidence_structural_execution_and_edge_case():
    # Structural + execution + edge-case confirmation -> 1.00
    conf = ConfidenceCalculator.calculate_confidence(
        has_structural_match=True,
        has_execution_evidence=True,
        has_edge_case_confirmation=True,
    )
    assert conf == 1.00


def test_confidence_execution_only():
    conf = ConfidenceCalculator.calculate_confidence(
        has_structural_match=False,
        has_execution_evidence=True,
        has_edge_case_confirmation=False,
    )
    assert conf == 0.90


def test_confidence_unknown_category():
    conf = ConfidenceCalculator.calculate_confidence(
        has_structural_match=False,
        has_execution_evidence=False,
        has_edge_case_confirmation=False,
        is_unknown=True,
    )
    assert conf == 0.50
