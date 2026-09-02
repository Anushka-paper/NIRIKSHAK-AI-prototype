import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.predictive.feature_builder import prepare_predictive_features

def test_prepare_predictive_features():
    df_work = pd.DataFrame({
        "canonical_work_id": ["W001", "W002"],
        "sanctioned_amount_inr": [100000.0, 200000.0],
        "sanction_delay_days": [10.0, 50.0]
    })
    X_scaled, df_m, feats = prepare_predictive_features(df_work)
    assert X_scaled.shape[0] == 2
    assert X_scaled.shape[1] == len(feats)
