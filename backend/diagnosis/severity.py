"""Evidence-driven deterministic severity calculation."""

from backend.diagnosis.models import DiscrepancyCategory, DiscrepancySeverity


class SeverityCalculator:
    """Calculates evidence-driven deterministic severity levels."""

    @staticmethod
    def calculate_severity(
        category: DiscrepancyCategory,
        affected_row_count: int,
        total_output_rows: int,
        affected_column_count: int = 1,
    ) -> DiscrepancySeverity:
        """Determine severity incorporating category, affected row percentage, and column impact."""
        if total_output_rows > 0:
            affected_pct = affected_row_count / total_output_rows
        else:
            affected_pct = 0.0

        # Structural-only differences with 0 affected rows
        if affected_row_count == 0:
            if category in (
                DiscrepancyCategory.BOUNDARY_CONDITION,
                DiscrepancyCategory.NULL_SEMANTICS,
                DiscrepancyCategory.JOIN_SEMANTICS,
            ):
                return DiscrepancySeverity.LOW
            return DiscrepancySeverity.INFO

        # Critical severity for major row cardinality shifts or > 25% population change
        if affected_pct >= 0.25 or (
            category == DiscrepancyCategory.JOIN_SEMANTICS and affected_pct >= 0.10
        ):
            return DiscrepancySeverity.CRITICAL

        # High severity for meaningful business rule or > 1% population change
        if affected_pct >= 0.01 or category in (
            DiscrepancyCategory.BOUNDARY_CONDITION,
            DiscrepancyCategory.NULL_SEMANTICS,
            DiscrepancyCategory.JOIN_SEMANTICS,
            DiscrepancyCategory.CASE_LOGIC,
        ):
            return DiscrepancySeverity.HIGH

        # Medium severity for localized differences
        if affected_pct > 0.0:
            return DiscrepancySeverity.MEDIUM

        return DiscrepancySeverity.LOW
