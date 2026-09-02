import pandas as pd

def check_numeric_validity(df, col):
    if col not in df.columns:
        return True
    numeric_s = pd.to_numeric(df[col], errors='coerce')
    return numeric_s.isna().sum() == df[col].isna().sum()
