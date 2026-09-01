import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
import pandas as pd
from data_pipeline.validation.rules.business import validate_business_rules

def test_business_rules():
    df = pd.DataFrame({
        "work_status": ["COMPLETED"],
        "completion_date": [None]
    })
    assert validate_business_rules(df) == 1
