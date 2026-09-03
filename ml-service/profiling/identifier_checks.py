import re
import pandas as pd

def check_format_consistency(series: pd.Series) -> dict:
    """Checks pattern consistency across string identifier values."""
    s_clean = series.dropna().astype(str).str.strip()
    if s_clean.empty:
        return {"distinct_patterns_count": 0, "dominant_pattern_pct": 100.0, "is_format_consistent": True}

    patterns = s_clean.apply(lambda val: re.sub(r'\d', 'D', re.sub(r'[a-zA-Z]', 'L', val)))
    pattern_counts = patterns.value_counts()
    top_freq = pattern_counts.iloc[0] if not pattern_counts.empty else 0
    dominant_pct = round((top_freq / len(s_clean)) * 100, 2)

    return {
        "distinct_patterns_count": int(len(pattern_counts)),
        "dominant_pattern_pct": dominant_pct,
        "is_format_consistent": bool(dominant_pct >= 90.0)
    }

def profile_identifier_column(series: pd.Series, col_name: str) -> dict:
    """Profiles identifier column attributes."""
    total_rows = len(series)
    non_null_s = series.dropna()
    missing_cnt = total_rows - len(non_null_s)
    unique_cnt = int(non_null_s.nunique())
    duplicate_id_cnt = len(non_null_s) - unique_cnt
    uniqueness_ratio = round((unique_cnt / (len(non_null_s) or 1)) * 100, 2)

    format_info = check_format_consistency(series)

    return {
        "column_name": col_name,
        "total_rows": total_rows,
        "unique_ids": unique_cnt,
        "duplicate_ids": duplicate_id_cnt,
        "missing_ids": missing_cnt,
        "uniqueness_ratio_pct": uniqueness_ratio,
        "format_consistency": format_info
    }

def run_identifier_checks(df: pd.DataFrame, id_columns: list) -> dict:
    """Runs identifier profiling for all detected ID columns."""
    profiles = {}
    for col in id_columns:
        if col in df.columns:
            profiles[col] = profile_identifier_column(df[col], col)
    return profiles
