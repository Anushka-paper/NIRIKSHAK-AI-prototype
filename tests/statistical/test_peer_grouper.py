import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.statistical.peer_grouper import assign_peer_groups

def test_assign_peer_groups():
    df_work = pd.DataFrame({
        "canonical_work_category": ["ROADS_AND_BRIDGES", "EDUCATION"],
        "canonical_state": ["BIHAR", "MAHARASHTRA"],
        "sanctioned_amount_inr": [300000.0, 3000000.0]
    })
    res = assign_peer_groups(df_work)
    assert res["project_size_tier"].iloc[0] == "SMALL"
    assert res["project_size_tier"].iloc[1] == "LARGE"
    assert res["peer_group_key"].iloc[0] == "ROADS_AND_BRIDGES::BIHAR::SMALL"
