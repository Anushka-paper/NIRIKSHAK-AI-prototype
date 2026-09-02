import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.ml_anomaly.preprocessor import prepare_feature_matrix

def test_prepare_feature_matrix():
    df_work = pd.DataFrame({
        "canonical_work_id": ["W001", "W002"],
        "sanction_delay_days": [10.0, 50.0],
        "overrun_pct": [0.0, 25.0]
    })
    X_scaled, df_m, feats = prepare_feature_matrix(df_work)
    assert X_scaled.shape[0] == 2
    assert X_scaled.shape[1] == len(feats)
