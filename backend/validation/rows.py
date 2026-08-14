import hashlib
import pandas as pd
from backend.core.models import RowValidationResult


class RowValidator:
    """Stage 2: Row-level Record Equivalence and Hash Comparison Validator."""

    @staticmethod
    def validate(source_df: pd.DataFrame, target_df: pd.DataFrame) -> RowValidationResult:
        source_count = len(source_df)
        target_count = len(target_df)

        if source_count == 0 and target_count == 0:
            return RowValidationResult(
                passed=True,
                source_row_count=0,
                target_row_count=0,
                matched_row_count=0,
                mismatched_row_count=0
            )

        # Normalize column ordering & convert to string representation for hashing
        src_sorted = source_df.reindex(sorted(source_df.columns), axis=1)
        tgt_sorted = target_df.reindex(sorted(target_df.columns), axis=1)

        src_hashes = set(src_sorted.apply(lambda r: hashlib.md5(str(tuple(r)).encode()).hexdigest(), axis=1))
        tgt_hashes = set(tgt_sorted.apply(lambda r: hashlib.md5(str(tuple(r)).encode()).hexdigest(), axis=1))

        matched = len(src_hashes.intersection(tgt_hashes))
        mismatched = max(source_count, target_count) - matched

        passed = (source_count == target_count) and (mismatched == 0)

        return RowValidationResult(
            passed=passed,
            source_row_count=source_count,
            target_row_count=target_count,
            matched_row_count=matched,
            mismatched_row_count=mismatched,
            sample_mismatches=[]
        )
