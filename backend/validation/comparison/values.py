"""Value comparison logic with explicit NULL semantics and configurable numeric tolerances."""

import math
from typing import Any, Tuple


def is_null_value(val: Any) -> bool:
    """Check if a value is considered NULL (None, NaN, pandas NA, or NoneType)."""
    if val is None:
        return True
    try:
        if isinstance(val, float) and math.isnan(val):
            return True
    except (TypeError, ValueError):
        pass
    if str(val) in ("<NA>", "NaN", "None", "null"):
        return True
    return False


def is_null_equivalent(val1: Any, val2: Any) -> Tuple[bool, bool]:
    """Check if both values are NULL, or if exactly one value is NULL.

    Returns (both_null, one_null).
    """
    null1 = is_null_value(val1)
    null2 = is_null_value(val2)

    if null1 and null2:
        return (True, False)
    if null1 or null2:
        return (False, True)
    return (False, False)


def compare_values(
    source_val: Any,
    target_val: Any,
    abs_tol: float = 1e-6,
    rel_tol: float = 1e-5,
) -> bool:
    """Compare two values for semantic equality.

    Handles explicit NULL semantics, numeric tolerances, and string/bool exact matching.
    """
    both_null, one_null = is_null_equivalent(source_val, target_val)
    if both_null:
        return True
    if one_null:
        return False

    # Try numeric tolerance comparison if both values can be cast to float
    try:
        f_src = float(source_val)
        f_tgt = float(target_val)
        diff = abs(f_src - f_tgt)
        if diff <= abs_tol:
            return True
        max_abs = max(abs(f_src), abs(f_tgt))
        if max_abs > 0 and (diff / max_abs) <= rel_tol:
            return True
        return False
    except (ValueError, TypeError):
        pass

    # Compare boolean values
    if isinstance(source_val, bool) or isinstance(target_val, bool):
        return bool(source_val) == bool(target_val)

    # String / generic representation comparison
    return str(source_val).strip() == str(target_val).strip()
