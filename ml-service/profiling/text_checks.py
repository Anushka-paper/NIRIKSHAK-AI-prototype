import pandas as pd
import numpy as np

def profile_text_column(series: pd.Series, col_name: str) -> dict:
    """Profiles free-text description columns."""
    total_rows = len(series)
    non_null_text = series.dropna().astype(str).str.strip()
    missing_cnt = total_rows - len(non_null_text)

    if len(non_null_text) == 0:
        return {
            "column_name": col_name,
            "missing_values": missing_cnt,
            "unique_values": 0,
            "duplicate_values": 0,
            "min_text_length": 0,
            "max_text_length": 0,
            "avg_text_length": 0.0,
            "median_text_length": 0.0,
            "avg_word_count": 0.0,
            "empty_descriptions_count": 0,
            "very_short_descriptions_count": 0
        }

    lengths = non_null_text.str.len()
    word_counts = non_null_text.str.split().str.len()

    unique_cnt = int(non_null_text.nunique())
    duplicate_cnt = len(non_null_text) - unique_cnt

    empty_desc_cnt = int((lengths == 0).sum())
    short_desc_cnt = int(((lengths > 0) & (lengths < 10)).sum())

    return {
        "column_name": col_name,
        "missing_values": missing_cnt,
        "unique_values": unique_cnt,
        "duplicate_values": duplicate_cnt,
        "min_text_length": int(lengths.min()),
        "max_text_length": int(lengths.max()),
        "avg_text_length": round(float(lengths.mean()), 1),
        "median_text_length": float(np.median(lengths)),
        "avg_word_count": round(float(word_counts.mean()), 1),
        "empty_descriptions_count": empty_desc_cnt,
        "very_short_descriptions_count": short_desc_cnt
    }

def run_text_checks(df: pd.DataFrame, text_cols: list) -> dict:
    """Runs text profiling on detected long-text columns."""
    profiles = {}
    for col in text_cols:
        if col in df.columns:
            profiles[col] = profile_text_column(df[col], col)
    return profiles
