import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
import pandas as pd
from data_pipeline.validation.rules.schema import validate_schema

def test_schema_required_columns():
    df = pd.DataFrame(columns=["source_house", "state", "work"])
    req = ["source_house", "state", "work"]
    assert validate_schema(df, req) == []
    
    df_missing = pd.DataFrame(columns=["state"])
    assert validate_schema(df_missing, req) == ["source_house", "work"]
