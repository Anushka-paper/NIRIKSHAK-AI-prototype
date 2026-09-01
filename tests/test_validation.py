import pytest
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_pipeline.validation.quality_score import calculate_quality_score
from data_pipeline.validation.engine import ValidationEngine

def test_quality_score_calculation():
    assert calculate_quality_score(1000, 0, 0) == 100.0
    assert calculate_quality_score(1000, 10, 20) == 94.0
    assert calculate_quality_score(0, 0, 0) == 100.0

def test_lok_sabha_validation_engine():
    engine = ValidationEngine("LOK_SABHA", "data/cleaned/lok_sabha")
    df_alloc = pd.DataFrame([{
        "source_house": "LOK_SABHA",
        "source_file": "clean_allocated_limit.csv",
        "source_row_number": 2,
        "state": "Maharashtra",
        "allocated_amount_₹": 83180553325.71
    }])
    res = engine.validate_dataset("allocated_limit", df_alloc)
    assert res["status"] in ["VALID", "VALID_WITH_WARNING"]
    assert res["errors"] == 0

def test_rajya_sabha_validation_engine():
    engine = ValidationEngine("RAJYA_SABHA", "data/cleaned/rajya_sabha")
    df_alloc = pd.DataFrame([{
        "source_house": "RAJYA_SABHA",
        "source_file": "clean_allocated_limit.csv",
        "source_row_number": 2,
        "state": "Kerala",
        "elected/nominated": "Elected MP",
        "allocated_amount_₹": 33638482301.82
    }])
    res = engine.validate_dataset("allocated_limit", df_alloc)
    assert res["status"] in ["VALID", "VALID_WITH_WARNING"]
    assert res["errors"] == 0
