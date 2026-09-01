import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.integration.multiplication_guard import pre_aggregate_expenditure

def test_multiplication_guard():
    df_exp = pd.DataFrame({
        "canonical_work_id": ["W001", "W001", "W002"],
        "expenditure_amount_inr": [100.0, 200.0, 300.0],
        "canonical_vendor_name": ["Vendor A", "Vendor A", "Vendor B"]
    })
    agg = pre_aggregate_expenditure(df_exp)
    assert len(agg) == 2
    assert agg[agg["canonical_work_id"] == "W001"]["expenditure_amount_inr"].iloc[0] == 300.0
