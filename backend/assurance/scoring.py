from backend.core.models import AssuranceScorecard, ValidationPipelineResult


class AssuranceScorer:
    """Calculates multi-factor 0-100 migration assurance score."""

    WEIGHTS = {
        "schema": 0.25,
        "rows": 0.30,
        "aggregates": 0.25,
        "business_rules": 0.10,
        "edge_cases": 0.10
    }

    @classmethod
    def calculate_score(cls, result: ValidationPipelineResult) -> AssuranceScorecard:
        breakdown = {}

        breakdown["schema"] = 100.0 if result.schema_check.passed else 0.0
        breakdown["rows"] = 100.0 if result.row_check.passed else 40.0
        breakdown["aggregates"] = 100.0 if result.aggregate_check.passed else 50.0

        rules_passed = sum(1 for r in result.business_rules_check if r.passed)
        total_rules = max(len(result.business_rules_check), 1)
        breakdown["business_rules"] = (rules_passed / total_rules) * 100.0

        breakdown["edge_cases"] = 100.0 if result.edge_cases_check.null_handling_passed else 60.0

        final_score = sum(breakdown[k] * cls.WEIGHTS[k] for k in cls.WEIGHTS)

        recommendations = []
        if final_score < 85.0:
            recommendations.append("Review row hash drift and schema column mappings before production release.")
        else:
            recommendations.append("High assurance score: Migration query verified for production deployment.")

        return AssuranceScorecard(
            migration_id=result.migration_id,
            assurance_score=round(final_score, 2),
            gate_passed=final_score >= 85.0,
            score_breakdown=breakdown,
            recommendations=recommendations
        )
