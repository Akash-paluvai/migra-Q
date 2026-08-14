import pandas as pd
from backend.validation.orchestrator import ValidationOrchestrator


def test_validation_orchestrator_passes_identical_dfs():
    df1 = pd.DataFrame({"id": [1, 2, 3], "amount": [10.0, 20.0, 30.0]})
    df2 = pd.DataFrame({"id": [1, 2, 3], "amount": [10.0, 20.0, 30.0]})

    result = ValidationOrchestrator.run_pipeline(df1, df2)
    assert result.passed is True
    assert result.overall_confidence_score == 100.0
