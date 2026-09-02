import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from data_pipeline.early_warning.alert_generator import generate_early_warning_alerts

def test_generate_early_warning_alerts():
    df_pred = pd.DataFrame([{
        "canonical_work_id": "WORK_101",
        "source_house": "LOK_SABHA",
        "canonical_state": "DELHI",
        "canonical_mp_name": "TEST MP",
        "project_risk_score": 85.0,
        "delay_probability": 0.90,
        "expected_delay_days": 120,
        "top_contributing_factors": "Sanction delay > 90 days; High cost variance",
        "recommended_monitoring_priority": "CRITICAL"
    }])
    
    df_comp = pd.DataFrame([{
        "entity_id": "WORK_101",
        "rule_code": "R003",
        "severity": "CRITICAL",
        "action": "Audit unsanctioned work"
    }])
    
    df_alerts = generate_early_warning_alerts(df_pred, df_comp, pd.DataFrame(), pd.DataFrame())
    assert not df_alerts.empty
    assert len(df_alerts) == 1
    
    alert = df_alerts.iloc[0].to_dict()
    assert alert["alert_id"] == "ALT_WORK_101"
    assert alert["priority"] == "CRITICAL"
    assert alert["status"] == "NEW"
    assert "Sanction delay" in alert["evidence_json"]

def test_empty_predictive_alerts():
    df_alerts = generate_early_warning_alerts(pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
    assert df_alerts.empty

