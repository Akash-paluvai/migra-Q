import pytest
import math
import numpy as np
import pandas as pd
from backend.validation.comparison.values import is_null_like, values_equal

def test_is_null_like():
    assert is_null_like(None)
    assert is_null_like(float('nan'))
    assert is_null_like(np.nan)
    assert is_null_like(pd.NA)
    assert is_null_like(pd.NaT)
    
    assert not is_null_like("NULL")
    assert not is_null_like("NaN")
    assert not is_null_like("null")
    assert not is_null_like("")
    assert not is_null_like(0)

def test_values_equal():
    # Null vs Null
    assert values_equal(None, None)
    assert values_equal(float('nan'), float('nan'))
    assert values_equal(None, float('nan'))
    assert values_equal(np.nan, None)
    assert values_equal(pd.NA, pd.NaT)
    
    # Null vs Non-null
    assert not values_equal(None, 10)
    assert not values_equal(float('nan'), 10)
    assert not values_equal("NULL", None)
    assert not values_equal("NaN", float('nan'))
    
    # String edge cases
    assert values_equal("nan", "nan")
    assert values_equal("NULL", "NULL")
    
    # Normal values
    assert values_equal(10, 10.0)
    assert values_equal("test", " test ")
    assert not values_equal(10, 11)

