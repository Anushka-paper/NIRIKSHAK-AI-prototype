import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.statistical.baselines import compute_peer_baselines
from data_pipeline.statistical.anomaly_evaluator import evaluate_statistical_anomalies

def test_evaluate_statistical_anomalies():
    df_work = pd.DataFrame({
        "canonical_work_id": ["W001", "W002", "W003", "W004"],
        "canonical_work_category": ["ROADS_AND_BRIDGES"] * 4,
        "canonical_state": ["BIHAR"] * 4,
        "sanctioned_amount_inr": [100000.0] * 4,
        "expenditure_amount_inr": [10000.0, 15000.0, 20000.0, 500000.0]
    })
    df_base = compute_peer_baselines(df_work)
    df_anom = evaluate_statistical_anomalies(df_work, df_base)
    assert len(df_anom) == 4
    assert bool(df_anom["iqr_amount_outlier"].iloc[3]) is True
