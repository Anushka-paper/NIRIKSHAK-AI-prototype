import pytest
import pandas as pd
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "ml-service"))

from profiling.profiler import DataProfiler, profile_dataset

def test_dynamic_profiler_schema_detection():
    df = pd.DataFrame({
        "Sr. No.": [1, 2],
        "State": ["UP", "TN"],
        "Allocated AMOUNT ( ₹ )": ["100000", "200000"],
        "Sanction Date": ["2024-01-01", "2024-01-02"]
    })

    profiler = DataProfiler(df=df, parliament="lok_sabha")
    report = profiler.profile(verbose=False)

    assert report["dataset"]["total_rows"] == 2
    assert report["dataset"]["columns_count"] == 4
    assert report["data_quality_score"] > 0
    assert len(report["schema"]) == 4

def test_missing_and_outlier_profiling():
    df = pd.DataFrame({
        "amount": [10, 20, 30, 40, 100000, None]
    })

    profiler = DataProfiler(df=df, parliament="rajya_sabha")
    report = profiler.profile(verbose=False)

    amt_profile = report["numeric_profiles"].get("amount", {})
    assert amt_profile["missing"] == 1
    assert amt_profile["outliers"]["outlier_count"] >= 1
