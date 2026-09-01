import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.integration.reconciliation import reconcile_financial_totals

def test_financial_reconciliation():
    source_sums = {"recommended_amount_inr": 1000.0, "sanctioned_amount_inr": 800.0}
    df_int = pd.DataFrame({"recommended_amount_inr": [1000.0], "sanctioned_amount_inr": [800.0]})
    report = reconcile_financial_totals(source_sums, df_int)
    assert report["recommended"]["diff"] == 0.0
    assert report["sanctioned"]["diff"] == 0.0
