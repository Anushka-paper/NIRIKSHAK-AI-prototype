import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.compliance.rules_work import evaluate_work_rules

def test_evaluate_work_rules():
    df_work = pd.DataFrame({
        "canonical_work_id": ["W001", "W002"],
        "source_house": ["LOK_SABHA", "LOK_SABHA"],
        "overrun_pct": [20.0, 0.0],
        "has_sanction": [False, True],
        "has_expenditure": [True, True],
        "sanction_delay_days": [-5.0, 10.0]
    })
    df_life = pd.DataFrame({
        "canonical_work_id": ["W001", "W002"],
        "sanctioned_amount_inr": [100000.0, 100000.0],
        "expenditure_amount_inr": [120000.0, 100000.0]
    })
    viols = evaluate_work_rules(df_work, df_life)
    assert len(viols) >= 2
    rule_codes = [v["rule_code"] for v in viols]
    assert "R002" in rule_codes
    assert "R003" in rule_codes
