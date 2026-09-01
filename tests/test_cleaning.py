import pytest
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_pipeline.cleaning.whitespace import clean_whitespace
from data_pipeline.cleaning.encoding import clean_encoding
from data_pipeline.cleaning.nulls import clean_null_value
from data_pipeline.cleaning.numeric import clean_numeric_val
from data_pipeline.cleaning.dates import clean_date_val
from data_pipeline.cleaning.metadata import is_grand_total_row, is_repeated_header_row

def test_whitespace_and_encoding():
    assert clean_whitespace("  Ravi Kishan  ") == "Ravi Kishan"
    assert clean_whitespace("Shri  Ravi  Kishan") == "Shri Ravi Kishan"
    assert clean_whitespace("  \t\nAdv  Dean Kuriakose\n ") == "Adv Dean Kuriakose"

def test_null_value_cleaning():
    assert clean_null_value("N/A") is None
    assert clean_null_value("n/a") is None
    assert clean_null_value("nan") is None
    assert clean_null_value("NULL") is None
    assert clean_null_value("  ") is None
    assert clean_null_value("0") == "0"
    assert clean_null_value("Valid Text") == "Valid Text"

def test_numeric_cleaning():
    val, valid = clean_numeric_val("? 83,18,05,53,325.71")
    assert valid is True
    assert val == 83180553325.71
    
    val_zero, valid_zero = clean_numeric_val("0")
    assert valid_zero is True
    assert val_zero == 0.0

    val_bad, valid_bad = clean_numeric_val("INVALID_AMOUNT_XYZ")
    assert valid_bad is False

def test_date_cleaning():
    d1, valid1 = clean_date_val("08-Jul-2024")
    assert valid1 is True
    assert d1 == "2024-07-08"
    
    d2, valid2 = clean_date_val("2024-04-01")
    assert valid2 is True
    assert d2 == "2024-04-01"

    d_bad, valid_bad = clean_date_val("31/02/2024")
    assert valid_bad is False

def test_metadata_stripping():
    row_gt = pd.Series(["Grand Total", "", "", "83,18,05,53,325.71"])
    assert is_grand_total_row(row_gt) is True
    
    cols = ["Sr. No.", "State", "MP Name", "Amount"]
    row_rep = pd.Series(["Sr. No.", "State", "MP Name", "Amount"])
    assert is_repeated_header_row(row_rep, cols) is True

def test_idempotency():
    val1 = clean_whitespace("  Shri  NK  Premachandran  ")
    val2 = clean_whitespace(val1)
    assert val1 == val2 == "Shri NK Premachandran"
