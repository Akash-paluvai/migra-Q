"""Edge Case Validator — evaluates Phase 2 benchmark scenarios against execution artifacts."""

import time
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

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


class EdgeCaseValidator(BaseValidator):
    """Validator for testing adversarial benchmark scenario edge cases against output artifacts."""

    name = "EdgeCaseValidator"

    def validate(self, context: ValidationContext) -> ValidationResult:
        start_time = time.perf_counter()

        scenario = context.benchmark_scenario
        src_exec = context.source_execution
        tgt_exec = context.target_execution

        df_src = _load_df(src_exec.result_artifact, src_exec.sample_data)
        df_tgt = _load_df(tgt_exec.result_artifact, tgt_exec.sample_data)

        if df_src is None or df_tgt is None:
            return ValidationResult(
                check_name=self.name,
                validator_version=VALIDATOR_VERSION,
                status=ValidationCheckStatus.SKIPPED,
                severity=ValidationSeverity.INFO,
                score=1.0,
                summary="Execution data unavailable for edge-case validation.",
                duration_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )

        evidence_items: list[EvidenceItem] = []
        mismatch_count = 0

        scenario_name = (
            scenario.get("scenario_name", "CUSTOM_EDGE_CASE") if scenario else "EDGE_CASE"
        )

        # Check NULL-value behavior in results
        null_src_count = int(df_src.isna().sum().sum())
        null_tgt_count = int(df_tgt.isna().sum().sum())

        if null_src_count != null_tgt_count:
            mismatch_count += 1
            if len(evidence_items) < context.config.max_evidence_items:
                evidence_items.append(
                    EvidenceItem(
                        type=EvidenceType.EDGE_CASE_FAILURE,
                        category="NULL_SEMANTICS",
                        source_value=null_src_count,
                        target_value=null_tgt_count,
                        detail=(
                            f"Edge scenario '{scenario_name}': NULL value count differs "
                            f"(source={null_src_count}, target={null_tgt_count})."
                        ),
                    )
                )

        # Check boundary condition values (e.g. 499.99, 500.00, 500.01 in results if available)
        boundary_vals = [499.99, 500.00, 500.01]
        for col in df_src.columns:
            if col in df_tgt.columns and pd.api.types.is_numeric_dtype(df_src[col]):
                for bval in boundary_vals:
                    src_has_b = (df_src[col] == bval).any()
                    tgt_has_b = (df_tgt[col] == bval).any()
                    if src_has_b and tgt_has_b:
                        # Compare classification/outcome for that boundary row
                        src_sub = df_src[df_src[col] == bval]
                        tgt_sub = df_tgt[df_tgt[col] == bval]

                        for key_col in context.config.comparison_key:
                            if key_col in src_sub.columns and key_col in tgt_sub.columns:
                                s_keys = set(src_sub[key_col].astype(str))
                                t_keys = set(tgt_sub[key_col].astype(str))
                                if s_keys != t_keys:
                                    mismatch_count += 1
                                    if len(evidence_items) < context.config.max_evidence_items:
                                        evidence_items.append(
                                            EvidenceItem(
                                                type=EvidenceType.EDGE_CASE_FAILURE,
                                                column=col,
                                                category="BOUNDARY_VALUE",
                                                source_value=list(s_keys),
                                                target_value=list(t_keys),
                                                detail=(
                                                    f"Boundary value {bval} in column '{col}' "
                                                    "diverged between source and target."
                                                ),
                                            )
                                        )

        score = 1.0 if mismatch_count == 0 else 0.0
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        status = ValidationCheckStatus.PASS if mismatch_count == 0 else ValidationCheckStatus.FAIL

        return ValidationResult(
            check_name=self.name,
            validator_version=VALIDATOR_VERSION,
            status=status,
            severity=ValidationSeverity.HIGH if mismatch_count > 0 else ValidationSeverity.INFO,
            score=round(score, 4),
            summary=(
                f"Edge case scenario '{scenario_name}': passed clean checks."
                if status == ValidationCheckStatus.PASS
                else f"Edge case failure in '{scenario_name}': {mismatch_count} failure(s)."
            ),
            mismatch_count=mismatch_count,
            evidence=evidence_items,
            evidence_truncated=mismatch_count > len(evidence_items),
            metadata={"scenario_name": scenario_name},
            duration_ms=duration_ms,
        )


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
