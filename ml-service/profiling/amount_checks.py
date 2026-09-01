import re
import pandas as pd
import numpy as np

def parse_currency_to_float(val) -> float | None:
    """
    Parses currency values including Indian formatting (₹ 1,47,00,000, 83,18,05,53,325.71)
    to clean numeric floats. Preserves original dataset value.
    """
    if pd.isna(val) or val is None or str(val).strip() == '':
        return None

    s = str(val).upper().strip()
    multiplier = 1.0

    if 'CRORE' in s or 'CR' in s:
        multiplier = 10000000.0
    elif 'LAKH' in s or 'L' in s.split():
        multiplier = 100000.0

    # Extract digits and decimal point
    cleaned_num = re.sub(r'[^\d.]', '', s)
    if not cleaned_num:
        return None

    try:
        # Handle multiple decimal points if malformed
        parts = cleaned_num.split('.')
        if len(parts) > 2:
            cleaned_num = parts[0] + '.' + ''.join(parts[1:])
        return float(cleaned_num) * multiplier
    except ValueError:
        return None

def profile_numeric_series(series: pd.Series, is_currency: bool = False) -> dict:
    """
    Profiles a numeric/currency column: calculates summary statistics, zero/neg/pos counts,
    and IQR outlier boundaries.
    """
    total_rows = len(series)

    if is_currency:
        numeric_series = series.apply(parse_currency_to_float)
    else:
        numeric_series = pd.to_numeric(series, errors='coerce')

    valid_series = numeric_series.dropna()
    valid_count = len(valid_series)
    missing_count = total_rows - valid_count

    if valid_count == 0:
        return {
            "count": 0,
            "missing": missing_count,
            "is_currency": is_currency,
            "stats": {}
        }

    q1 = float(np.percentile(valid_series, 25))
    q2 = float(np.percentile(valid_series, 50)) # median
    q3 = float(np.percentile(valid_series, 75))
    iqr = float(q3 - q1)

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outliers = valid_series[(valid_series < lower_bound) | (valid_series > upper_bound)]
    outlier_count = int(len(outliers))
    outlier_pct = round((outlier_count / valid_count) * 100, 2)

    zero_count = int((valid_series == 0).sum())
    neg_count = int((valid_series < 0).sum())
    pos_count = int((valid_series > 0).sum())

    stats = {
        "count": valid_count,
        "missing": missing_count,
        "total_sum": float(valid_series.sum()) if is_currency else None,
        "minimum": float(valid_series.min()),
        "maximum": float(valid_series.max()),
        "mean": round(float(valid_series.mean()), 2),
        "median": round(q2, 2),
        "std_dev": round(float(valid_series.std()), 2) if valid_count > 1 else 0.0,
        "variance": round(float(valid_series.var()), 2) if valid_count > 1 else 0.0,
        "q1": round(q1, 2),
        "q2": round(q2, 2),
        "q3": round(q3, 2),
        "iqr": round(iqr, 2),
        "zero_count": zero_count,
        "negative_count": neg_count,
        "positive_count": pos_count,
        "outliers": {
            "outlier_count": outlier_count,
            "outlier_percentage": outlier_pct,
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2)
        }
    }

    return stats

def run_amount_checks(df: pd.DataFrame, numeric_cols: list, currency_cols: list) -> dict:
    """Runs numeric and currency profiling on detected columns."""
    profiles = {}
    for col in currency_cols:
        if col in df.columns:
            profiles[col] = profile_numeric_series(df[col], is_currency=True)

    for col in numeric_cols:
        if col in df.columns and col not in profiles:
            profiles[col] = profile_numeric_series(df[col], is_currency=False)

    return profiles

