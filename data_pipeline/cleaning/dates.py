import pandas as pd
from datetime import datetime

def clean_date_val(val):
    if val is None or pd.isna(val):
        return None, True
        
    val_str = str(val).strip()
    if not val_str or val_str.lower() in {'n/a', 'na', 'null', 'nan', 'none', '-'}:
        return None, True
        
    if val_str.isdigit():
        try:
            excel_date = pd.to_datetime(int(val_str), unit='D', origin='1899-12-30')
            return excel_date.strftime('%Y-%m-%d'), True
        except Exception:
            pass

    date_formats = [
        '%d-%b-%Y', '%d-%B-%Y', '%d/%m/%Y', '%Y-%m-%d',
        '%d-%m-%Y', '%Y/%m/%d', '%d-%b-%y', '%d/%m/%y'
    ]
    
    for fmt in date_formats:
        try:
            parsed = datetime.strptime(val_str, fmt)
            if 1950 <= parsed.year <= 2035:
                return parsed.strftime('%Y-%m-%d'), True
        except ValueError:
            continue
            
    try:
        parsed = pd.to_datetime(val_str, dayfirst=True, errors='raise')
        if 1950 <= parsed.year <= 2035:
            return parsed.strftime('%Y-%m-%d'), True
    except Exception:
        pass
        
    return None, False
