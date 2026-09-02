import pandas as pd

def validate_iso_dates(df):
    date_cols = [c for c in df.columns if "date" in c or "completion" in c or "consent" in c]
    invalid_dates = {}
    for col in date_cols:
        s = df[col].dropna().astype(str)
        # Check ISO format YYYY-MM-DD
        is_iso = s.str.match(r'^\d{4}-\d{2}-\d{2}$')
        bad_count = int((~is_iso).sum())
        if bad_count > 0:
            invalid_dates[col] = bad_count
    return invalid_dates
