"""Row Validator — key-based relational comparison of source and target result sets."""

import time

from backend.validation.comparison.relations import compare_relations
from backend.validation.context import ValidationContext
from backend.validation.exceptions import ComparisonKeyError
from backend.validation.models import (
    VALIDATOR_VERSION,
    ValidationCheckStatus,
    ValidationResult,
    ValidationSeverity,
)
from backend.validation.validators.base import BaseValidator


class RowValidator(BaseValidator):
    """Validator for row-level semantic comparison across result sets."""

    name = "RowValidator"

    def validate(self, context: ValidationContext) -> ValidationResult:
        start_time = time.perf_counter()

        keys = context.config.comparison_key
        if not keys:
            return ValidationResult(
                check_name=self.name,
                validator_version=VALIDATOR_VERSION,
                status=ValidationCheckStatus.ERROR,
                severity=ValidationSeverity.HIGH,
                score=0.0,
                summary="Comparison key required for row-level semantic comparison.",
                duration_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )

        src_exec = context.source_execution
        tgt_exec = context.target_execution

        try:
            res = compare_relations(
                source_artifact=src_exec.result_artifact,
                target_artifact=tgt_exec.result_artifact,
                source_sample=src_exec.sample_data,
                target_sample=tgt_exec.sample_data,
                comparison_keys=keys,
                abs_tol=context.config.numeric_absolute_tolerance,
                rel_tol=context.config.numeric_relative_tolerance,
                max_evidence_items=context.config.max_evidence_items,
            )
        except ComparisonKeyError as exc:
            return ValidationResult(
                check_name=self.name,
                validator_version=VALIDATOR_VERSION,
                status=ValidationCheckStatus.ERROR,
                severity=ValidationSeverity.HIGH,
                score=0.0,
                summary=f"Row comparison key error: {exc}",
                duration_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        mismatch_count = res["mismatch_count"]
        status = ValidationCheckStatus.PASS if mismatch_count == 0 else ValidationCheckStatus.FAIL

        return ValidationResult(
            check_name=self.name,
            validator_version=VALIDATOR_VERSION,
            status=status,
            severity=ValidationSeverity.CRITICAL if mismatch_count > 0 else ValidationSeverity.INFO,
            score=res["score"],
            summary=(
                f"Row comparison: {res['rows_matched']}/{res['rows_compared']} "
                "keys matched exactly."
                if status == ValidationCheckStatus.PASS
                else f"Row mismatch detected: {mismatch_count} value/key discrepancy(ies)."
            ),
            expected={"total_rows": src_exec.row_count},
            actual={"total_rows": tgt_exec.row_count},
            mismatch_count=mismatch_count,
            evidence=res["evidence"],
            evidence_truncated=res["evidence_truncated"],
            metadata={
                "comparison_keys": keys,
                "rows_compared": res["rows_compared"],
                "rows_matched": res["rows_matched"],
                "missing_source_keys": res["missing_source_keys"],
                "extra_target_keys": res["extra_target_keys"],
                "duplicate_key_warnings": res["duplicate_key_warnings"],
            },
            duration_ms=duration_ms,
        )
