import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.statistical.baselines import compute_peer_baselines

def test_compute_peer_baselines():
    df_work = pd.DataFrame({
        "canonical_work_category": ["ROADS_AND_BRIDGES"] * 5,
        "canonical_state": ["BIHAR"] * 5,
        "sanctioned_amount_inr": [100000.0] * 5,
        "expenditure_amount_inr": [10000.0, 20000.0, 30000.0, 40000.0, 50000.0]
    })
    res = compute_peer_baselines(df_work)
    assert len(res) == 1
    assert res["exp_mean"].iloc[0] == 30000.0
    assert res["exp_q1"].iloc[0] == 20000.0
    assert res["exp_q3"].iloc[0] == 40000.0
