import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.features.transaction_features import compute_transaction_features

def test_compute_transaction_features():
    df_exp = pd.DataFrame({
        "transaction_id": ["TXN_001"],
        "canonical_work_id": ["W001"],
        "canonical_vendor_name": ["Vendor A"],
        "expenditure_amount_inr": [100000.0]
    })
    df_life = pd.DataFrame({
        "canonical_work_id": ["W001"],
        "sanctioned_amount_inr": [100000.0],
        "canonical_work_category": ["ROADS_AND_BRIDGES"]
    })
    res = compute_transaction_features(df_exp, df_life)
    assert len(res) == 1
    assert bool(res["is_round_amount"].iloc[0]) is True
    assert res["expenditure_to_sanction_pct"].iloc[0] == 100.0
