import re
import pandas as pd

def clean_numeric_val(val, field_name="numeric_field"):
    if val is None or pd.isna(val):
        return None, True
    if isinstance(val, (int, float)):
        return float(val), True
    
    val_str = str(val).strip()
    if not val_str or val_str.lower() in {'n/a', 'na', 'null', 'nan', 'none', '-'}:
        return None, True
        
    clean_str = re.sub(r'[^0-9.-]', '', val_str)
    try:
        num_val = float(clean_str)
        return num_val, True
    except ValueError:
        return None, False
