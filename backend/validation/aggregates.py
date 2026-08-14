import numpy as np
import pandas as pd
from backend.core.models import AggregateValidationResult


class AggregateValidator:
    """Stage 3: Aggregate Metric & Grouping Invariants Validator."""

    @staticmethod
    def validate(source_df: pd.DataFrame, target_df: pd.DataFrame) -> AggregateValidationResult:
        diffs = {}
        metrics_compared = []

        num_cols = source_df.select_dtypes(include=[np.number]).columns

        for col in num_cols:
            if col in target_df.columns:
                metrics_compared.append(f"SUM({col})")
                src_sum = float(source_df[col].sum())
                tgt_sum = float(target_df[col].sum())
                diffs[f"SUM({col})_delta"] = round(abs(src_sum - tgt_sum), 4)

                metrics_compared.append(f"AVG({col})")
                src_avg = float(source_df[col].mean()) if len(source_df) > 0 else 0.0
                tgt_avg = float(target_df[col].mean()) if len(target_df) > 0 else 0.0
                diffs[f"AVG({col})_delta"] = round(abs(src_avg - tgt_avg), 4)

        passed = all(v == 0.0 for v in diffs.values())

        return AggregateValidationResult(
            passed=passed,
            metrics_compared=metrics_compared,
            diffs=diffs
        )
