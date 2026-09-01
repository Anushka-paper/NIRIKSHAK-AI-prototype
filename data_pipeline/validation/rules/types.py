import pandas as pd

def validate_numeric_columns(df):
    amount_cols = [c for c in df.columns if "amount" in c or "limit" in c or "disbursed" in c]
    invalid_cols = []
    for col in amount_cols:
        numeric_s = pd.to_numeric(df[col], errors='coerce')
        if numeric_s.isna().sum() > df[col].isna().sum():
            invalid_cols.append(col)
    return invalid_cols
