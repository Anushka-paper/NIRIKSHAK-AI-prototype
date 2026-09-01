import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
from data_pipeline.entity_resolution.work_id_parser import parse_work_id

def test_work_id_parser():
    res = parse_work_id("WS/MP620/2024-2025/133166")
    assert res["is_esakshi"] is True
    assert res["house"] == "LOK_SABHA"
    assert res["mp_code"] == "MP620"
    assert res["financial_year"] == "2024-2025"
