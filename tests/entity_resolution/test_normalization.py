import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
from data_pipeline.entity_resolution.normalizers import normalize_name, normalize_vendor, normalize_ida

def test_name_normalization():
    assert normalize_name("Shri Ravi Kishan") == "ravi kishan"
    assert normalize_name("Dr. Shashi Tharoor") == "shashi tharoor"

def test_vendor_normalization():
    assert normalize_vendor("ABC Const. Pvt. Ltd.") == "abc construction private limited"

def test_ida_normalization():
    assert normalize_ida("P.W.D. Gorakhpur") == "public works department gorakhpur"
