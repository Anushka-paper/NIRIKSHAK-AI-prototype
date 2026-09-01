import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
import pandas as pd
from data_pipeline.validation.rules.dates import validate_iso_dates
from data_pipeline.validation.rules.date_sequences import validate_date_sequence

def test_iso_date_validation():
    df = pd.DataFrame({"recommended_date": ["2024-04-01", "2024-05-10"]})
    assert validate_iso_dates(df) == {}

def test_date_sequence_validation():
    df_bad = pd.DataFrame({
        "recommended_date": ["2024-05-10"],
        "sanction_date": ["2024-04-01"]
    })
    assert validate_date_sequence(df_bad) == 1
