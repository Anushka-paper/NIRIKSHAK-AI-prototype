import pandas as pd
from data_pipeline.cleaning.whitespace import clean_whitespace

NULL_PATTERNS = {'n/a', 'na', 'null', 'none', 'nan', 'not available', 'blank', '', 'n.a.'}

def clean_null_value(val):
    if val is None or pd.isna(val):
        return None
    if isinstance(val, str):
        cleaned_str = clean_whitespace(val)
        if cleaned_str.lower() in NULL_PATTERNS:
            return None
        return cleaned_str
    return val
