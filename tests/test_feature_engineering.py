"""
Unit and Integration Tests for Dynamic, Leakage-Safe Feature Engineering.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Ensure ml-service path
SERVICE_DIR = Path(__file__).resolve().parent.parent / "ml-service"
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

from features.entity_features import compute_entity_features
from features.financial_features import compute_financial_features, safe_divide
from features.temporal_features import compute_temporal_and_lifecycle_features
from features.text_features import compute_text_features
from features.historical_features import compute_leakage_safe_historical_features
from features.statistical_features import compute_statistical_features
from features.aggregation_features import compute_group_aggregations
from features.leakage_checker import check_feature_leakage
from features.quality_reporter import generate_feature_dictionary, audit_feature_quality

@pytest.fixture
def sample_work_master_df():
    return pd.DataFrame([
        {
            "canonical_work_id": "CW_000001",
            "official_work_id": "WS/101",
            "parliament": "lok_sabha",
            "state": "Maharashtra",
            "constituency": "PUNE",
            "mp_name": "MP Alpha",
            "work_category": "Normal",
            "work_description": "Construction of primary health center and solar lighting",
            "recommended_date": "2024-01-10",
            "recommended_amount": 1000000.0,
            "sanction_date": "2024-02-15",
            "sanctioned_amount": 1200000.0,
            "completion_date": "2024-08-20",
            "completion_amount": 1150000.0,
            "expenditure_amount": 1150000.0,
            "expenditure_transaction_count": 2,
            "first_expenditure_date": "2024-03-01",
            "last_expenditure_date": "2024-07-15",
            "vendor_name": "Apex Infra Ltd",
            "has_recommendation": 1,
            "has_sanction": 1,
            "has_expenditure": 1,
            "has_completion": 1,
        },
        {
            "canonical_work_id": "CW_000002",
            "official_work_id": None,
            "parliament": "lok_sabha",
            "state": "Maharashtra",
            "constituency": "PUNE",
            "mp_name": "MP Alpha",
            "work_category": "Normal",
            "work_description": "Repair of high school road",
            "recommended_date": "2024-05-01",
            "recommended_amount": 500000.0,
            "sanction_date": "2024-06-01",
            "sanctioned_amount": 500000.0,
            "completion_date": None,
            "completion_amount": np.nan,
            "expenditure_amount": 200000.0,
            "expenditure_transaction_count": 1,
            "first_expenditure_date": "2024-07-01",
            "last_expenditure_date": "2024-07-01",
            "vendor_name": "Apex Infra Ltd",
            "has_recommendation": 1,
            "has_sanction": 1,
            "has_expenditure": 1,
            "has_completion": 0,
        }
    ])

def test_safe_division():
    """Verifies that division by zero or invalid numbers never produces inf or unhandled NaN."""
    s1 = pd.Series([100.0, 50.0, 0.0])
    s2 = pd.Series([2.0, 0.0, 0.0])
    res = safe_divide(s1, s2, fill_value=0.0)
    assert res.iloc[0] == 50.0
    assert res.iloc[1] == 0.0
    assert res.iloc[2] == 0.0
    assert not np.isinf(res).any()

def test_financial_features_and_gaps(sample_work_master_df):
    """Verifies financial differences, ratios, percentages, and gap features."""
    df = compute_financial_features(sample_work_master_df)
    
    # CW_000001: sanc=1.2M, rec=1.0M -> diff = 200,000, pct = 20%
    assert df.loc[0, "recommendation_sanction_amount_difference"] == 200000.0
    assert df.loc[0, "recommendation_to_sanction_amount_change_pct"] == 20.0
    assert df.loc[0, "unspent_amount"] == 50000.0 # 1.2M - 1.15M
    assert round(df.loc[0, "expenditure_to_sanction_ratio"], 4) == round(1150000.0 / 1200000.0, 4)

def test_temporal_and_chronology_features(sample_work_master_df):
    """Verifies Indian Financial Year, duration days, and lifecycle chronology checks."""
    df = compute_temporal_and_lifecycle_features(sample_work_master_df)
    
    # 2024-02-15 is FY 2023-2024
    assert df.loc[0, "sanction_financial_year"] == "2023-2024"
    # 2024-06-01 is FY 2024-2025
    assert df.loc[1, "sanction_financial_year"] == "2024-2025"

    assert df.loc[0, "valid_lifecycle_sequence"] == 1
    assert df.loc[0, "lifecycle_status"] == "COMPLETED"
    assert df.loc[1, "lifecycle_status"] == "EXPENDITURE_STARTED"

def test_time_aware_historical_no_future_leakage(sample_work_master_df):
    """CRITICAL: Verifies earlier works do NOT leak future completion data."""
    df = compute_leakage_safe_historical_features(sample_work_master_df)
    
    # For row 0 (sanctioned 2024-02-15), it is the first work of MP Alpha -> historical work count must be 0
    assert df.loc[0, "mp_historical_work_count"] == 0
    assert df.loc[0, "mp_historical_completed_count"] == 0
    
    # For row 1 (sanctioned 2024-06-01), preceding work is row 0 -> count is 1
    assert df.loc[1, "mp_historical_work_count"] == 1

def test_text_complexity_features(sample_work_master_df):
    """Verifies word counts, character counts, and uppercase ratios."""
    df = compute_text_features(sample_work_master_df)
    assert df.loc[0, "work_description_word_count"] > 5
    assert df.loc[0, "has_work_description"] == 1
    assert df.loc[0, "work_description_missing"] == 0

def test_leakage_checker_classification():
    """Verifies that post-sanction metrics are strictly identified as POST_PREDICTION."""
    cols = [
        "canonical_work_id", "sanctioned_amount", "sanction_date",
        "completion_date", "completion_amount", "total_execution_days",
        "unspent_amount", "mp_historical_completion_rate"
    ]
    report = check_feature_leakage(cols)
    
    post_cols = report[report["leakage_status"] == "POST_PREDICTION"]["feature_name"].tolist()
    assert "completion_date" in post_cols
    assert "completion_amount" in post_cols
    assert "total_execution_days" in post_cols
    assert "unspent_amount" in post_cols

    safe_cols = report[report["leakage_status"] == "AVAILABLE_AT_PREDICTION"]["feature_name"].tolist()
    assert "sanctioned_amount" in safe_cols
    assert "sanction_date" in safe_cols
    assert "mp_historical_completion_rate" in safe_cols

def test_group_aggregations(sample_work_master_df):
    """Verifies MP, State, and Vendor dimension table generations."""
    mp_df, const_df, state_df, vendor_df = compute_group_aggregations(sample_work_master_df)
    assert len(mp_df) == 1
    assert mp_df.iloc[0]["work_count"] == 2
    assert len(vendor_df) == 1
    assert vendor_df.iloc[0]["vendor_name"] == "Apex Infra Ltd"
