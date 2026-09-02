import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
import pandas as pd
from data_pipeline.standardisation.dates import standardise_date_column

def test_date_standardisation():
    df = pd.DataFrame({"recommended_date": ["2024-04-01", "08-Jul-2024"]})
    df_std = standardise_date_column(df, "recommended_date", "recommended_date")
    assert "raw_recommended_date" in df_std.columns
    assert df_std["recommended_date"].tolist() == ["2024-04-01", "2024-07-08"]
