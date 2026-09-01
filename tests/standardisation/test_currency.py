import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
import pandas as pd
from data_pipeline.standardisation.currency import standardise_currency_column

def test_currency_standardisation():
    df = pd.DataFrame({"sanction_amount_₹": [100000.0, 250000.5]})
    df_std = standardise_currency_column(df, "sanction_amount_₹", "sanctioned_amount_inr")
    assert "raw_sanction_amount_₹" in df_std.columns
    assert df_std["sanctioned_amount_inr"].tolist() == [100000.0, 250000.5]
