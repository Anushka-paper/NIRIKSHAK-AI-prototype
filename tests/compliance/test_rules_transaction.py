import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.compliance.rules_transaction import evaluate_transaction_rules

def test_evaluate_transaction_rules():
    df_txn = pd.DataFrame({
        "transaction_id": ["TXN_001"],
        "canonical_work_id": ["W001"],
        "days_since_sanction": [-10.0]
    })
    viols = evaluate_transaction_rules(df_txn)
    assert len(viols) == 1
    assert viols[0]["rule_code"] == "R001"
    assert viols[0]["severity"] == "CRITICAL"
