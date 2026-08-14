from backend.core.config import settings
from backend.core.models import AssuranceScorecard


class QualityGateEvaluator:
    """CI/CD Deployment Quality Gate Evaluator."""

    @staticmethod
    def evaluate(scorecard: AssuranceScorecard, min_threshold: float | None = None) -> bool:
        threshold = min_threshold if min_threshold is not None else settings.MIN_ASSURANCE_SCORE_PASS
        return scorecard.assurance_score >= threshold
