import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.features.work_features import compute_work_features

def test_compute_work_features():
    df_life = pd.DataFrame({
        "canonical_work_id": ["W001"],
        "source_house": ["LOK_SABHA"],
        "canonical_work_category": ["ROADS_AND_BRIDGES"],
        "recommended_date": ["2024-01-01"],
        "sanction_date": ["2024-01-11"],
        "completion_date": ["2024-02-10"],
        "recommended_amount_inr": [100000.0],
        "sanctioned_amount_inr": [120000.0],
        "expenditure_amount_inr": [130000.0],
        "work": ["Construction of rural road"]
    })
    res = compute_work_features(df_life)
    assert len(res) == 1
    assert res["sanction_delay_days"].iloc[0] == 10.0
    assert round(res["estimate_variance_pct"].iloc[0], 2) == 20.0
    assert round(res["overrun_pct"].iloc[0], 2) == 8.33
