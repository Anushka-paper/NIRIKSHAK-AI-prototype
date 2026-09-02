import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.compliance.evaluator import ComplianceEvaluator

def test_compliance_evaluator():
    evaluator = ComplianceEvaluator()
    df_work = pd.DataFrame({"canonical_work_id": ["W001"], "sanction_delay_days": [-5.0]})
    df_life = pd.DataFrame({"canonical_work_id": ["W001"]})
    df_txn = pd.DataFrame()
    
    df_viol = evaluator.run_all_evaluations(df_work, df_life, df_txn)
    assert len(df_viol) == 1
    assert df_viol["rule_code"].iloc[0] == "R004"
