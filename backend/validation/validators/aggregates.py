"""Aggregate Validator — compares aggregate statistics between source and target result sets."""

import time
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from backend.validation.comparison.values import compare_values
from backend.validation.context import ValidationContext
from backend.validation.models import (
    VALIDATOR_VERSION,
    EvidenceItem,
    EvidenceType,
    ValidationCheckStatus,
    ValidationResult,
    ValidationSeverity,
)
from backend.validation.validators.base import BaseValidator


class AggregateValidator(BaseValidator):
    """Validator for comparing aggregate statistics (COUNT, SUM, AVG, MIN, MAX, COUNT DISTINCT)."""

    name = "AggregateValidator"

    def validate(self, context: ValidationContext) -> ValidationResult:
        start_time = time.perf_counter()

        src_exec = context.source_execution
        tgt_exec = context.target_execution

        df_src = _load_df(src_exec.result_artifact, src_exec.sample_data)
        df_tgt = _load_df(tgt_exec.result_artifact, tgt_exec.sample_data)

        if df_src is None or df_tgt is None:
            return ValidationResult(
                check_name=self.name,
                validator_version=VALIDATOR_VERSION,
                status=ValidationCheckStatus.ERROR,
                severity=ValidationSeverity.HIGH,
                score=0.0,
                summary="Execution data unavailable for aggregate validation.",
                duration_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )

        evidence_items: list[EvidenceItem] = []
        mismatch_count = 0
        total_aggregates = 0
        matched_aggregates = 0

        # Determine target numeric and count candidate columns
        src_cols = [c.name for c in src_exec.columns]
        tgt_cols = [c.name for c in tgt_exec.columns]
        common_cols = [c for c in src_cols if c in tgt_cols]

        specs = context.config.aggregate_specs
        if not specs:
            # Generate default specs for numeric columns and count for table
            specs = [{"column": "*", "functions": ["COUNT"]}]
            for c in src_exec.columns:
                if c.name in common_cols and c.type in (
                    "INTEGER",
                    "BIGINT",
                    "FLOAT",
                    "DOUBLE",
                    "DECIMAL",
                    "NUMERIC",
                    "INT",
                    "INT64",
                    "FLOAT8",
                ):
                    specs.append({"column": c.name, "functions": ["SUM", "AVG", "MIN", "MAX"]})

        for spec in specs:
            col = spec["column"]
            fns = spec["functions"]

            for fn in fns:
                fn_upper = fn.upper()
                total_aggregates += 1

                val_src = _compute_stat(df_src, col, fn_upper)
                val_tgt = _compute_stat(df_tgt, col, fn_upper)

                is_match = compare_values(
                    val_src,
                    val_tgt,
                    abs_tol=context.config.numeric_absolute_tolerance,
                    rel_tol=context.config.numeric_relative_tolerance,
                )

                if is_match:
                    matched_aggregates += 1
                else:
                    mismatch_count += 1
                    if len(evidence_items) < context.config.max_evidence_items:
                        evidence_items.append(
                            EvidenceItem(
                                type=EvidenceType.AGGREGATE_MISMATCH,
                                column=col,
                                source_value=val_src,
                                target_value=val_tgt,
                                detail=(
                                    f"Aggregate {fn_upper}({col}) mismatch: "
                                    f"source={val_src}, target={val_tgt}."
                                ),
                            )
                        )

        score = (matched_aggregates / total_aggregates) if total_aggregates > 0 else 1.0
        score = max(0.0, min(1.0, score))

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        status = ValidationCheckStatus.PASS if mismatch_count == 0 else ValidationCheckStatus.FAIL

        return ValidationResult(
            check_name=self.name,
            validator_version=VALIDATOR_VERSION,
            status=status,
            severity=ValidationSeverity.HIGH if mismatch_count > 0 else ValidationSeverity.INFO,
            score=round(score, 4),
            summary=(
                f"Aggregate validation: {matched_aggregates}/{total_aggregates} metrics matched."
                if status == ValidationCheckStatus.PASS
                else f"Aggregate mismatch detected: {mismatch_count} metric discrepancy(ies)."
            ),
            mismatch_count=mismatch_count,
            evidence=evidence_items,
            evidence_truncated=mismatch_count > len(evidence_items),
            metadata={
                "total_aggregates": total_aggregates,
                "matched_aggregates": matched_aggregates,
            },
            duration_ms=duration_ms,
        )


def _compute_stat(df: pd.DataFrame, col: str, fn: str) -> Any:
    """Compute SQL aggregate stat respecting SQL NULL semantics."""
    if fn == "COUNT":
        return len(df) if col == "*" else int(df[col].dropna().count())
    if col not in df.columns:
        return None
    s = df[col].dropna()
    if len(s) == 0:
        return None
    if fn == "SUM":
        return float(s.sum())
    if fn == "AVG":
        return float(s.mean())
    if fn == "MIN":
        return float(s.min())
    if fn == "MAX":
        return float(s.max())
    if fn == "COUNT_DISTINCT":
        return int(s.nunique())
    return None


def _load_df(
    artifact_path: str | Path | None,
    sample_data: list[dict[str, Any]] | None,
) -> pd.DataFrame | None:
    """Load DataFrame helper."""
    if artifact_path and Path(artifact_path).exists():
        try:
            return duckdb.sql(f"SELECT * FROM read_parquet('{artifact_path}')").df()
        except Exception:
            pass
    if sample_data is not None:
        return pd.DataFrame(sample_data)
    return None
