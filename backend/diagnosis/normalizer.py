"""Expression normalization and deterministic signature generation."""

import hashlib
import re


def normalize_expression(expr: str | None) -> str:
    """Normalize SQL/AST expression for stable hashing and identity comparison."""
    if not expr:
        return ""
    # Strip leading/trailing spaces, collapse inner whitespace
    s = re.sub(r"\s+", " ", expr.strip())
    # Strip trailing decimals for whole floats (e.g. 500.00 or 500.0 -> 500)
    s = re.sub(r"(\d+)\.0+(?!\d)", r"\1", s)
    # Standardize uppercase for standard SQL keywords
    s = re.sub(
        r"\b(select|from|where|join|left|right|inner|outer|on|group|by|having|order|case|when|then|else|end|is|null|not|and|or|sum|count|avg|min|max|distinct|cast|as)\b",
        lambda m: m.group(1).upper(),
        s,
        flags=re.IGNORECASE,
    )
    return s


def compute_discrepancy_signature(
    category: str,
    analysis_path: str,
    source_expr: str | None,
    target_expr: str | None,
) -> str:
    """Compute deterministic discrepancy signature string and hash.

    Signature = category + analysis_path + norm_source + norm_target
    """
    norm_src = normalize_expression(source_expr)
    norm_tgt = normalize_expression(target_expr)
    raw_sig = f"{category}:{analysis_path}:{norm_src}:{norm_tgt}"
    return hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()[:16]
