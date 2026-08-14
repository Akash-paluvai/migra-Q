import pandas as pd
from backend.core.models import BusinessRuleResult


class BusinessRulesValidator:
    """Stage 4: Domain & Business Rules Assertions Engine."""

    @staticmethod
    def validate(source_df: pd.DataFrame, target_df: pd.DataFrame) -> list[BusinessRuleResult]:
        results = []

        # Rule 1: Non-negative ID rule
        if "id" in source_df.columns and "id" in target_df.columns:
            src_valid = (source_df["id"] >= 0).all()
            tgt_valid = (target_df["id"] >= 0).all()
            results.append(
                BusinessRuleResult(
                    rule_name="NonNegativeID",
                    passed=bool(src_valid and tgt_valid),
                    description="All ID keys must be non-negative integers"
                )
            )

        # Rule 2: Non-null keys
        if len(source_df.columns) > 0 and len(target_df.columns) > 0:
            first_col = source_df.columns[0]
            src_nulls = source_df[first_col].isnull().sum()
            tgt_nulls = target_df[first_col].isnull().sum()
            results.append(
                BusinessRuleResult(
                    rule_name="PrimaryKeyNotNull",
                    passed=bool(src_nulls == 0 and tgt_nulls == 0),
                    description="Primary key column must not contain NULL values"
                )
            )

        return results
