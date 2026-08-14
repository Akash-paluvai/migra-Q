import pandas as pd
from backend.core.models import SchemaValidationResult


class SchemaValidator:
    """Stage 1: Schema Integrity and Column Alignment Validator."""

    @staticmethod
    def validate(source_df: pd.DataFrame, target_df: pd.DataFrame) -> SchemaValidationResult:
        source_cols = [c.lower() for c in source_df.columns]
        target_cols = [c.lower() for c in target_df.columns]

        missing = [c for c in source_cols if c not in target_cols]
        type_mismatches = []

        for col in source_cols:
            if col in target_cols:
                src_type = str(source_df[source_df.columns[source_cols.index(col)]].dtype)
                tgt_type = str(target_df[target_df.columns[target_cols.index(col)]].dtype)
                if src_type != tgt_type:
                    type_mismatches.append({"column": col, "source_type": src_type, "target_type": tgt_type})

        passed = len(missing) == 0

        return SchemaValidationResult(
            passed=passed,
            source_columns=list(source_df.columns),
            target_columns=list(target_df.columns),
            missing_columns=missing,
            type_mismatches=type_mismatches
        )
