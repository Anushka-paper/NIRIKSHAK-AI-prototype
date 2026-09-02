import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
import pandas as pd
from data_pipeline.standardisation.categories import map_category, standardise_categories

def test_category_mapping():
    assert map_category("Construction of Road") == "ROADS_AND_BRIDGES"
    assert map_category("Water Tank") == "DRINKING_WATER"
    assert map_category("School Building") == "EDUCATION"
