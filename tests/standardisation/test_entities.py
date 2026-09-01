import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
import pandas as pd
from data_pipeline.standardisation.entities import clean_mp_name

def test_mp_name_cleaning():
    assert clean_mp_name("  Shri Ravi Kishan  ") == "RAVI KISHAN"
    assert clean_mp_name("Dr. Shashi Tharoor") == "SHASHI THAROOR"
