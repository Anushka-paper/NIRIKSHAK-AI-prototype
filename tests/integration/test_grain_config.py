import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from data_pipeline.integration.config import DATASET_GRAIN_CONFIG

def test_grain_configuration():
    assert DATASET_GRAIN_CONFIG["works_recommended"]["grain"] == "work-level"
    assert DATASET_GRAIN_CONFIG["expenditure"]["grain"] == "expenditure-transaction-level"
