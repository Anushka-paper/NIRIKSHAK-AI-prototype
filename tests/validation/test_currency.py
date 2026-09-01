import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
import pandas as pd
from data_pipeline.validation.rules.currency import validate_currency_rules

def test_currency_non_negativity():
    df_bad = pd.DataFrame({"sanction_amount_₹": [100.0, -50.0]})
    negs, _ = validate_currency_rules(df_bad)
    assert negs.get("sanction_amount_₹") == 1
