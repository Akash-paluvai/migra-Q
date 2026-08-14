import pandas as pd
from typing import Dict, Any, List


class MismatchDetector:
    """Detects specific cell-level and row-level diffs between source and target DataFrames."""

    @staticmethod
    def find_cell_mismatches(source_df: pd.DataFrame, target_df: pd.DataFrame) -> List[Dict[str, Any]]:
        mismatches = []
        common_cols = [c for c in source_df.columns if c in target_df.columns]
        min_rows = min(len(source_df), len(target_df))

        for idx in range(min_rows):
            for col in common_cols:
                v1 = source_df.iloc[idx][col]
                v2 = target_df.iloc[idx][col]
                if str(v1) != str(v2):
                    mismatches.append({
                        "row_index": idx,
                        "column": col,
                        "source_value": str(v1),
                        "target_value": str(v2)
                    })
        return mismatches
