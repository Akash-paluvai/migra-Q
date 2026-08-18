"""Relational comparison engine for key-based row comparison across result sets."""

from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from backend.validation.comparison.values import values_equal
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

    # Fast path: Vectorized comparison if unique 1:1 keys and matching index lengths
    if (
        not missing_in_target
        and not extra_in_target
        and len(df_src) == len(df_tgt)
        and df_src["_join_key"].is_unique
        and df_tgt["_join_key"].is_unique
    ):
        df_src_sorted = df_src.sort_values("_join_key").reset_index(drop=True)
        df_tgt_sorted = df_tgt.sort_values("_join_key").reset_index(drop=True)

        for col in common_cols:
            s_series = df_src_sorted[col]
            t_series = df_tgt_sorted[col]

            # Vectorized fast check to isolate potential mismatches
            mismatches = s_series != t_series
            potential_diff_indices = df_src_sorted.index[mismatches]
            
            # Refine mismatches with robust scalar equality
            actual_diff_indices = []
            for idx in potential_diff_indices:
                if not values_equal(s_series.loc[idx], t_series.loc[idx], abs_tol=abs_tol, rel_tol=rel_tol):
                    actual_diff_indices.append(idx)
                    
            diff_count = len(actual_diff_indices)

            if diff_count > 0:
                mismatch_count += diff_count
                for idx in actual_diff_indices[:max_evidence_items]:
                    if len(evidence_items) < max_evidence_items:
                        key_dict = {col_k: str(df_src_sorted.loc[idx, col_k]) for col_k in comparison_keys}
                        evidence_items.append(
                            EvidenceItem(
                                type=EvidenceType.VALUE_MISMATCH,
                                key=key_dict,
                                column=col,
                                source_value=s_series.loc[idx],
                                target_value=t_series.loc[idx],
                                category="VALUE_MISMATCH",
                                detail=f"Value mismatch in column '{col}': '{s_series.loc[idx]}' vs '{t_series.loc[idx]}'",
                            )
                        )
            rows_matched = len(df_src_sorted) - diff_count

        return {
            "mismatch_count": mismatch_count,
            "rows_compared": len(df_src),
            "rows_matched": max(0, rows_matched),
            "missing_source_keys": 0,
            "extra_target_keys": 0,
            "duplicate_key_warnings": 0,
            "evidence": evidence_items,
            "evidence_truncated": mismatch_count > max_evidence_items,
            "score": round(max(0.0, (len(df_src) - mismatch_count) / max(1, len(df_src))), 4),
        }

    src_grouped = df_src.groupby("_join_key")
    tgt_grouped = df_tgt.groupby("_join_key")

    for k in sorted(list(common_keys)):
        src_sub = src_grouped.get_group(k)
        tgt_sub = tgt_grouped.get_group(k)

        if len(src_sub) > 1 or len(tgt_sub) > 1:
            duplicate_key_warnings += 1

        src_rows_list = [row.to_dict() for _, row in src_sub.iterrows()]
        tgt_rows_list = [row.to_dict() for _, row in tgt_sub.iterrows()]

        matched_pairs = _match_group_rows(
            src_rows_list, tgt_rows_list, common_cols, abs_tol=abs_tol, rel_tol=rel_tol
        )

        for r_src, r_tgt in matched_pairs:
            if r_src is None and r_tgt is not None:
                mismatch_count += 1
                if len(evidence_items) < max_evidence_items:
                    key_dict = {col: str(r_tgt[col]) for col in comparison_keys}
                    evidence_items.append(
                        EvidenceItem(
                            type=EvidenceType.MISSING_SOURCE_ROW,
                            key=key_dict,
                            category="EXTRA_IN_TARGET",
                            detail=f"Duplicate key {key_dict} has extra row in target.",
                        )
                    )
                continue

            if r_tgt is None and r_src is not None:
                mismatch_count += 1
                if len(evidence_items) < max_evidence_items:
                    key_dict = {col: str(r_src[col]) for col in comparison_keys}
                    evidence_items.append(
                        EvidenceItem(
                            type=EvidenceType.MISSING_TARGET_ROW,
                            key=key_dict,
                            category="MISSING_FROM_TARGET",
                            detail=f"Duplicate key {key_dict} has extra row in source.",
                        )
                    )
                continue

            if r_src is not None and r_tgt is not None:
                row_has_mismatch = False
                key_dict = {col: str(r_src[col]) for col in comparison_keys}

                for col in common_cols:
                    val_s = r_src[col]
                    val_t = r_tgt[col]

                    if not values_equal(val_s, val_t, abs_tol=abs_tol, rel_tol=rel_tol):
                        row_has_mismatch = True
                        mismatch_count += 1
                        if len(evidence_items) < max_evidence_items:
                            evidence_items.append(
                                EvidenceItem(
                                    type=EvidenceType.VALUE_MISMATCH,
                                    key=key_dict,
                                    column=col,
                                    source_value=val_s,
                                    target_value=val_t,
                                    category="VALUE_MISMATCH",
                                    detail=f"Column '{col}' mismatch for key {key_dict}.",
                                )
                            )

                if not row_has_mismatch:
                    rows_matched += 1

    if duplicate_key_warnings > 0 and len(evidence_items) < max_evidence_items:
        evidence_items.append(
            EvidenceItem(
                type=EvidenceType.DUPLICATE_KEY_WARNING,
                category="NON_UNIQUE_KEY_WARNING",
                detail=(
                    f"Comparison key {comparison_keys} is non-unique across "
                    f"{duplicate_key_warnings} key groups."
                ),
            )
        )

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


def _match_group_rows(
    src_rows: list[dict[str, Any]],
    tgt_rows: list[dict[str, Any]],
    common_cols: list[str],
    abs_tol: float = 1e-6,
    rel_tol: float = 1e-5,
) -> list[tuple[dict[str, Any] | None, dict[str, Any] | None]]:
    """Match rows within a single duplicate key group using multiset alignment.

    1. Identical rows (all common_cols match) are paired first.
    2. Remaining rows are paired greedily to maximize matching columns.
    3. Unmatched rows are returned paired with None.
    """
    src_unmatched = list(range(len(src_rows)))
    tgt_unmatched = list(range(len(tgt_rows)))

    pairs: list[tuple[dict[str, Any] | None, dict[str, Any] | None]] = []

    # 1. Exact match pass
    src_to_remove = []
    tgt_to_remove = []

    for i in src_unmatched:
        r_src = src_rows[i]
        for j in tgt_unmatched:
            if j in tgt_to_remove:
                continue
            r_tgt = tgt_rows[j]
            all_match = True
            for col in common_cols:
                if not values_equal(r_src[col], r_tgt[col], abs_tol=abs_tol, rel_tol=rel_tol):
                    all_match = False
                    break
            if all_match:
                pairs.append((r_src, r_tgt))
                src_to_remove.append(i)
                tgt_to_remove.append(j)
                break

    src_remaining = [i for i in src_unmatched if i not in src_to_remove]
    tgt_remaining = [j for j in tgt_unmatched if j not in tgt_to_remove]

    # 2. Maximum column match pass for remaining rows
    while src_remaining and tgt_remaining:
        best_pair = None
        best_match_count = -1

        for i in src_remaining:
            r_src = src_rows[i]
            for j in tgt_remaining:
                r_tgt = tgt_rows[j]
                match_count = sum(
                    1
                    for col in common_cols
                    if values_equal(r_src[col], r_tgt[col], abs_tol=abs_tol, rel_tol=rel_tol)
                )
                if match_count > best_match_count:
                    best_match_count = match_count
                    best_pair = (i, j)

        if best_pair:
            i, j = best_pair
            pairs.append((src_rows[i], tgt_rows[j]))
            src_remaining.remove(i)
            tgt_remaining.remove(j)
        else:
            break

    # 3. Add remaining unmatched rows
    for i in src_remaining:
        pairs.append((src_rows[i], None))
    for j in tgt_remaining:
        pairs.append((None, tgt_rows[j]))

    return pairs


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
