import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.integration.lifecycle_builder import build_unified_work_lifecycle_table

def test_lifecycle_builder():
    df_rec = pd.DataFrame({"canonical_work_id": ["W001"], "work": ["Road Work"], "recommended_date": ["2024-04-01"]})
    df_sanc = pd.DataFrame({"canonical_work_id": ["W001"], "sanction_date": ["2024-05-01"]})
    df_comp = pd.DataFrame()
    df_exp = pd.DataFrame()
    
    master = build_unified_work_lifecycle_table(df_rec, df_sanc, df_comp, df_exp)
    assert len(master) == 1
    assert bool(master["has_recommendation"].iloc[0]) is True
    assert bool(master["has_sanction"].iloc[0]) is True
    assert bool(master["has_completion"].iloc[0]) is False
    assert master["lifecycle_stage"].iloc[0] == "SANCTIONED"
