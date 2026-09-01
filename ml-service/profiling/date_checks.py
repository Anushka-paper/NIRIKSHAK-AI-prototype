import re
import pandas as pd
from datetime import datetime

def parse_date_series(series: pd.Series) -> pd.Series:
    """Parses date string series into datetime objects with dayfirst=True fallback."""
    return pd.to_datetime(series, errors='coerce', dayfirst=True)

def profile_date_column(series: pd.Series, col_name: str) -> dict:
    """Profiles date column bounds, missing, invalid, and future dates."""
    total_rows = len(series)
    non_null_raw = series.dropna()
    missing_count = total_rows - len(non_null_raw)

    parsed_series = parse_date_series(series)
    valid_dates = parsed_series.dropna()
    invalid_count = len(non_null_raw) - len(valid_dates)

    if len(valid_dates) == 0:
        return {
            "column_name": col_name,
            "total_rows": total_rows,
            "missing_dates": missing_count,
            "invalid_dates": invalid_count,
            "future_dates": 0,
            "min_date": None,
            "max_date": None
        }

    now = datetime.now()
    future_dates = int((valid_dates > now).sum())

    return {
        "column_name": col_name,
        "total_rows": total_rows,
        "missing_dates": missing_count,
        "invalid_dates": invalid_count,
        "future_dates": future_dates,
        "min_date": valid_dates.min().strftime('%Y-%m-%d'),
        "max_date": valid_dates.max().strftime('%Y-%m-%d')
    }

def check_date_sequence_anomalies(df: pd.DataFrame, date_columns: list) -> list:
    """
    Checks semantic date sequence rules if multiple date columns exist in dataset:
    - Recommended date > Sanction Date
    - Sanction Date > Completion Date
    """
    anomalies = []
    if len(date_columns) < 2:
        return anomalies

    rec_col = next((c for c in date_columns if 'rec' in c.lower()), None)
    sanc_col = next((c for c in date_columns if 'sanc' in c.lower()), None)
    comp_col = next((c for c in date_columns if 'comp' in c.lower()), None)

    if rec_col and sanc_col and rec_col in df.columns and sanc_col in df.columns:
        dt_rec = parse_date_series(df[rec_col])
        dt_sanc = parse_date_series(df[sanc_col])

        violations = (dt_sanc < dt_rec).sum()
        if violations > 0:
            anomalies.append({
                "rule": f"{sanc_col} < {rec_col}",
                "description": f"Sanction date occurs before recommendation date",
                "violation_count": int(violations)
            })

    if sanc_col and comp_col and sanc_col in df.columns and comp_col in df.columns:
        dt_sanc = parse_date_series(df[sanc_col])
        dt_comp = parse_date_series(df[comp_col])

        violations = (dt_comp < dt_sanc).sum()
        if violations > 0:
            anomalies.append({
                "rule": f"{comp_col} < {sanc_col}",
                "description": f"Completion date occurs before sanction date",
                "violation_count": int(violations)
            })

    return anomalies

def run_date_checks(df: pd.DataFrame, date_columns: list) -> dict:
    """Runs date profiling and sequence anomaly checks across all date columns."""
    col_profiles = {}
    for col in date_columns:
        if col in df.columns:
            col_profiles[col] = profile_date_column(df[col], col)

    sequence_anomalies = check_date_sequence_anomalies(df, date_columns)

    return {
        "columns": col_profiles,
        "sequence_anomalies": sequence_anomalies
    }
