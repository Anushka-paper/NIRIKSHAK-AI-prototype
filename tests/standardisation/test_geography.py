import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
import pandas as pd
from data_pipeline.standardisation.geography import standardise_geography

def test_geography_standardisation():
    df = pd.DataFrame({"state": ["Maharashtra  "], "constituency": ["hingoli"]})
    df_std = standardise_geography(df, "LOK_SABHA")
    assert df_std["canonical_state"].iloc[0] == "MAHARASHTRA"
    assert df_std["canonical_constituency"].iloc[0] == "HINGOLI"
    assert df_std["canonical_state_id"].iloc[0] == "STATE_MAHARASHTRA"
