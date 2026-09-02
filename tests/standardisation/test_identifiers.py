import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from data_pipeline.standardisation.identifiers import standardise_identifiers

def test_work_id_generation():
    df = pd.DataFrame({"work_id": ["WS/MP620/12345", None], "source_house": ["LOK_SABHA", "LOK_SABHA"], "canonical_state": ["MH", "MH"], "canonical_mp_name": ["ABC", "ABC"], "work": ["Road", "Road"], "recommended_date": ["2024-04-01", "2024-04-01"]})
    df_std = standardise_identifiers(df)
    assert df_std["canonical_work_id"].iloc[0] == "WS/MP620/12345"
    assert df_std["canonical_work_id"].iloc[1].startswith("WORK_HASH_")
