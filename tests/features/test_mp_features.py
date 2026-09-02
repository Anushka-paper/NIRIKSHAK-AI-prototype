import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.features.mp_features import compute_mp_features

def test_compute_mp_features():
    df_mp = pd.DataFrame({"mp_id": ["MP001"], "canonical_name": ["MP A"], "source_house": ["LOK_SABHA"]})
    df_life = pd.DataFrame({
        "canonical_mp_name": ["MP A"],
        "has_recommendation": [True],
        "has_sanction": [True],
        "has_completion": [True],
        "sanction_delay_days": [5.0],
        "expenditure_amount_inr": [10000000.0],
        "canonical_work_category": ["ROADS_AND_BRIDGES"]
    })
    res = compute_mp_features(df_mp, df_life, pd.DataFrame())
    assert len(res) == 1
    assert res["completed_count"].iloc[0] == 1
