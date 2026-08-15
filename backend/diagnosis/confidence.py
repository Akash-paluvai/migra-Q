"""Rule-based classification confidence calculation."""


class ConfidenceCalculator:
    """Calculates deterministic classification confidence scores based on evidence strength."""

    @staticmethod
    def calculate_confidence(
        has_structural_match: bool,
        has_execution_evidence: bool,
        has_edge_case_confirmation: bool,
        is_unknown: bool = False,
    ) -> float:
        """Compute rule-based evidence-strength classification confidence score.

        Note: Classification confidence score is a deterministic evidence-strength score,
        not a statistical/ML probability.
        """
        if is_unknown:
            return 0.50

        if has_structural_match and has_execution_evidence and has_edge_case_confirmation:
            return 1.00

        if has_structural_match and has_execution_evidence:
            return 0.95

        if has_execution_evidence and not has_structural_match:
            return 0.90

        if has_structural_match and not has_execution_evidence:
            return 0.85

        return 0.60
