import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from data_pipeline.compliance.duplicate_payment_engine import run_duplicate_payment_detection

def test_exact_duplicate_detection():
    df_txn = pd.DataFrame([
        {"canonical_work_id": "W1", "canonical_vendor_name": "VENDOR_A", "amount_inr": 50000, "transaction_date": "2024-01-10"},
        {"canonical_work_id": "W1", "canonical_vendor_name": "VENDOR_A", "amount_inr": 50000, "transaction_date": "2024-01-10"},
    ])
    
    df_res = run_duplicate_payment_detection(df_txn)
    assert not df_res.empty
    assert len(df_res) >= 1
    assert "EXACT" in df_res["layer_type"].values

def test_rate_card_baseline_detection():
    txns = []
    for i in range(6):
        txns.append({"canonical_work_id": f"W_{i}", "canonical_vendor_name": f"VENDOR_{i}", "amount_inr": 36159, "transaction_date": "2024-01-10"})
        txns.append({"canonical_work_id": f"W_{i}", "canonical_vendor_name": f"VENDOR_{i}", "amount_inr": 36159, "transaction_date": "2024-01-10"})
    
    df_res = run_duplicate_payment_detection(pd.DataFrame(txns))
    assert not df_res.empty
    assert df_res.iloc[0]["rate_card_baseline_flag"] == True
    assert df_res.iloc[0]["status"] == "LEGITIMATE_RATE_CARD"

