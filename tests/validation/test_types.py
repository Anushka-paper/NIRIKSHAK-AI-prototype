import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
import pandas as pd
from data_pipeline.validation.rules.types import validate_numeric_columns

def test_numeric_type_checks():
    df_good = pd.DataFrame({"sanction_amount_₹": [100.0, 200.5]})
    assert validate_numeric_columns(df_good) == []
