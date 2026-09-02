import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.features.vendor_features import compute_vendor_features

def test_compute_vendor_features():
    df_vm = pd.DataFrame({"vendor_id": ["V001"], "canonical_name": ["Vendor A"]})
    df_exp = pd.DataFrame({"canonical_work_id": ["W001"], "canonical_vendor_name": ["Vendor A"], "expenditure_amount_inr": [50000.0]})
    df_life = pd.DataFrame({"canonical_work_id": ["W001"], "canonical_constituency": ["Constituency 1"], "canonical_mp_name": ["MP A"]})
    
    res = compute_vendor_features(df_vm, df_exp, df_life)
    assert len(res) == 1
    assert res["total_expenditure_inr"].iloc[0] == 50000.0
