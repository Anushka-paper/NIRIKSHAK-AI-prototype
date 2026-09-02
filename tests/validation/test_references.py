import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
import pandas as pd
from data_pipeline.validation.rules.references import validate_work_references

def test_referential_integrity():
    df_exp = pd.DataFrame({"work_id": ["W001", "W002"]})
    df_works = pd.DataFrame({"work_id": ["W001"]})
    assert validate_work_references(df_exp, df_works) == 1
