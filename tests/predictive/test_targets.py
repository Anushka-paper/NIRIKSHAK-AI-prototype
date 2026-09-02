import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.predictive.targets import generate_target_labels

def test_generate_target_labels():
    df_work = pd.DataFrame({
        "canonical_work_id": ["W001", "W002"],
        "sanction_delay_days": [10.0, 50.0],
        "completion_delay_days": [0.0, 100.0],
        "has_sanction": [True, True],
        "has_expenditure": [True, False],
        "inactivity_gap_days": [10.0, 200.0]
    })
    df_life = pd.DataFrame()
    res = generate_target_labels(df_work, df_life)
    assert res["is_delayed"].iloc[1] == 1
    assert res["is_stagnant"].iloc[1] == 1
