import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
import pandas as pd
from data_pipeline.validation.rules.nulls import profile_nulls

def test_null_profiling():
    df = pd.DataFrame({
        "work": ["Work A", None],
        "image": [None, None]
    })
    prof = profile_nulls(df, ["work"])
    assert prof["work"]["null_count"] == 1
    assert prof["work"]["classification"] == "REQUIRED"
    assert prof["image"]["classification"] == "OPTIONAL"
