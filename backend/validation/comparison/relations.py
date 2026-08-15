"""Relational comparison engine for key-based row comparison across result sets."""

from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from backend.validation.comparison.values import compare_values
from backend.validation.exceptions import ComparisonKeyError
from backend.validation.models import EvidenceItem, EvidenceType


def compare_relations(
    source_artifact: str | Path | None,
    target_artifact: str | Path | None,
    source_sample: list[dict[str, Any]] | None,
    target_sample: list[dict[str, Any]] | None,
    comparison_keys: list[str],
    abs_tol: float = 1e-6,
    rel_tol: float = 1e-5,
    max_evidence_items: int = 100,
) -> dict[str, Any]:
    """Compare two relation outputs using primary comparison keys.

    Returns dict containing mismatch summary statistics and representative evidence.
    """
    df_src = _load_df(source_artifact, source_sample)
    df_tgt = _load_df(target_artifact, target_sample)

    if df_src is None or df_tgt is None:
        raise ComparisonKeyError("Source or target execution data is missing.")

    # Check key columns exist
    for key in comparison_keys:
        if key not in df_src.columns:
            raise ComparisonKeyError(f"Comparison key '{key}' not found in source schema.")
        if key not in df_tgt.columns:
            raise ComparisonKeyError(f"Comparison key '{key}' not found in target schema.")

    common_cols = [c for c in df_src.columns if c in df_tgt.columns and c not in comparison_keys]

    # Convert key values to string for stable grouping
    df_src["_join_key"] = df_src[comparison_keys].astype(str).agg(":".join, axis=1)
    df_tgt["_join_key"] = df_tgt[comparison_keys].astype(str).agg(":".join, axis=1)

    src_keys = set(df_src["_join_key"].unique())
    tgt_keys = set(df_tgt["_join_key"].unique())

    missing_in_target = src_keys - tgt_keys
    extra_in_target = tgt_keys - src_keys
    common_keys = src_keys & tgt_keys

    evidence_items: list[EvidenceItem] = []
    mismatch_count = 0

    # 1. Capture missing rows from target
    for k in sorted(list(missing_in_target)):
        mismatch_count += 1
        if len(evidence_items) < max_evidence_items:
            row_match = df_src[df_src["_join_key"] == k].iloc[0]
            key_dict = {col: str(row_match[col]) for col in comparison_keys}
            evidence_items.append(
                EvidenceItem(
                    type=EvidenceType.MISSING_TARGET_ROW,
                    key=key_dict,
                    category="MISSING_FROM_TARGET",
                    detail=f"Key {key_dict} present in source but missing in target.",
                )
            )

    # 2. Capture extra rows in target
    for k in sorted(list(extra_in_target)):
        mismatch_count += 1
        if len(evidence_items) < max_evidence_items:
            row_match = df_tgt[df_tgt["_join_key"] == k].iloc[0]
            key_dict = {col: str(row_match[col]) for col in comparison_keys}
            evidence_items.append(
                EvidenceItem(
                    type=EvidenceType.MISSING_SOURCE_ROW,
                    key=key_dict,
                    category="EXTRA_IN_TARGET",
                    detail=f"Key {key_dict} present in target but missing in source.",
                )
            )

    # 3. Compare value differences for common keys
    rows_matched = 0
    duplicate_key_warnings = 0

    src_grouped = df_src.groupby("_join_key")
    tgt_grouped = df_tgt.groupby("_join_key")

    for k in sorted(list(common_keys)):
        src_rows = src_grouped.get_group(k)
        tgt_rows = tgt_grouped.get_group(k)

        if len(src_rows) > 1 or len(tgt_rows) > 1:
            duplicate_key_warnings += 1

        pair_count = max(len(src_rows), len(tgt_rows))
        for i in range(pair_count):
            if i >= len(src_rows):
                mismatch_count += 1
                continue
            if i >= len(tgt_rows):
                mismatch_count += 1
                continue

            r_src = src_rows.iloc[i]
            r_tgt = tgt_rows.iloc[i]
            row_has_mismatch = False
            key_dict = {col: str(r_src[col]) for col in comparison_keys}

            for col in common_cols:
                val_s = r_src[col]
                val_t = r_tgt[col]

                if not compare_values(val_s, val_t, abs_tol=abs_tol, rel_tol=rel_tol):
                    row_has_mismatch = True
                    mismatch_count += 1
                    if len(evidence_items) < max_evidence_items:
                        evidence_items.append(
                            EvidenceItem(
                                type=EvidenceType.VALUE_MISMATCH,
                                key=key_dict,
                                column=col,
                                source_value=str(val_s),
                                target_value=str(val_t),
                                category="VALUE_MISMATCH",
                                detail=f"Column '{col}' mismatch for key {key_dict}.",
                            )
                        )

            if not row_has_mismatch:
                rows_matched += 1

    total_rows = len(df_src)
    score = (rows_matched / total_rows) if total_rows > 0 else (1.0 if len(df_tgt) == 0 else 0.0)
    score = max(0.0, min(1.0, score))

    return {
        "rows_compared": len(common_keys),
        "rows_matched": rows_matched,
        "missing_source_keys": len(missing_in_target),
        "extra_target_keys": len(extra_in_target),
        "duplicate_key_warnings": duplicate_key_warnings,
        "mismatch_count": mismatch_count,
        "score": round(score, 4),
        "evidence": evidence_items,
        "evidence_truncated": mismatch_count > len(evidence_items),
    }


def _load_df(
    artifact_path: str | Path | None,
    sample_data: list[dict[str, Any]] | None,
) -> pd.DataFrame | None:
    """Load DataFrame from Parquet artifact or fallback to sample_data array."""
    if artifact_path and Path(artifact_path).exists():
        try:
            return duckdb.sql(f"SELECT * FROM read_parquet('{artifact_path}')").df()
        except Exception:
            pass

    if sample_data is not None:
        return pd.DataFrame(sample_data)

    return None
