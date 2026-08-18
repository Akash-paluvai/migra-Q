"""Value comparison logic with explicit NULL semantics and configurable numeric tolerances."""

import math
from typing import Any, Tuple
import pandas as pd


def is_null_like(val: Any) -> bool:
    """Check if a value is considered NULL (None, NaN, pandas NA, NaT)."""
    if val is None:
        return True
    
    if val is pd.NA or val is pd.NaT:
        return True

    try:
        if isinstance(val, float) and math.isnan(val):
            return True
    except (TypeError, ValueError):
        pass

    return False


def values_equal(
    source_val: Any,
    target_val: Any,
    abs_tol: float = 1e-6,
    rel_tol: float = 1e-5,
) -> bool:
    """Semantic equality for validator scalar values."""
    source_null = is_null_like(source_val)
    target_null = is_null_like(target_val)

    if source_null and target_null:
        return True

    if source_null != target_null:
        return False

    # Try numeric tolerance comparison if both values can be cast to float
    try:
        f_src = float(source_val)
        f_tgt = float(target_val)
        if math.isnan(f_src) or math.isnan(f_tgt):
            pass # Fallback to string comparison for literal "nan" strings
        else:
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
