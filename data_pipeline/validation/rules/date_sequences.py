import pandas as pd

def validate_date_sequence(df):
    if "recommended_date" in df.columns and "sanction_date" in df.columns:
        rec_dates = pd.to_datetime(df["recommended_date"], errors='coerce')
        sanc_dates = pd.to_datetime(df["sanction_date"], errors='coerce')
        invalid_seq = int((sanc_dates < rec_dates).sum())
        return invalid_seq
    return 0
