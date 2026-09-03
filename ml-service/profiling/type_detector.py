import re
import pandas as pd
import numpy as np
import warnings

# Suppress dateutil parsing warnings during sample checks
warnings.filterwarnings('ignore', category=UserWarning)

# Keyword Patterns with exact word boundaries
ID_KEYWORDS = r'(?i)\b(id|code|sr\.?\s*no\.?|serial|ida|work_id|project_id|application_id|ref)\b'
CURRENCY_KEYWORDS = r'(?i)\b(amount|allocated|allocation|sanction|expenditure|cost|fund|budget|₹|rs|inr)\b'
DATE_KEYWORDS = r'(?i)\b(date|day|time|month|year|timestamp|dt)\b'

def detect_column_type(series: pd.Series, column_name: str) -> str:
    """
    Dynamically infer detected column type using dtype, column name semantics,
    value patterns, and cardinality.
    Possible detected types:
      - identifier
      - currency
      - numeric
      - date
      - boolean
      - text
      - categorical
      - unknown
    """
    col_clean = str(column_name).strip()
    non_null_series = series.dropna()
    total_valid = len(non_null_series)

    if total_valid == 0:
        return "unknown"

    sample_vals = non_null_series.astype(str).str.strip()

    # 1. Identifier Check (ID, Code, Sr. No., IDA)
    if re.search(ID_KEYWORDS, col_clean):
        return "identifier"

    unique_ratio = non_null_series.nunique() / total_valid if total_valid > 0 else 0
    if unique_ratio > 0.95 and not pd.api.types.is_float_dtype(series):
        avg_len = sample_vals.str.len().mean()
        if avg_len < 40:
            return "identifier"

    # 2. Date / Datetime Check (Check Date FIRST before currency so Date columns are not misclassified!)
    if re.search(DATE_KEYWORDS, col_clean):
        return "date"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"

    if sample_vals.dtype == object:
        sample_subset = sample_vals.head(50)
        try:
            parsed_dates = pd.to_datetime(sample_subset, errors='coerce', dayfirst=True)
            if parsed_dates.notnull().sum() / len(sample_subset) > 0.8:
                return "date"
        except Exception:
            pass

    # 3. Currency Check
    if re.search(CURRENCY_KEYWORDS, col_clean):
        return "currency"

    currency_symbol_matches = sample_vals.str.contains(r'[₹$€£]', regex=True).sum()
    if currency_symbol_matches / total_valid > 0.3:
        return "currency"

    # 4. Boolean Check
    unique_lower = set(sample_vals.str.lower().unique())
    bool_sets = [
        {'true', 'false'}, {'yes', 'no'}, {'y', 'n'}, {'0', '1'},
        {'true'}, {'false'}, {'yes'}, {'no'}
    ]
    if any(unique_lower.issubset(b_set) for b_set in bool_sets):
        return "boolean"

    # 5. Numeric Check
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    try:
        cleaned_num = sample_vals.str.replace(r'[\$,₹,]', '', regex=True)
        converted = pd.to_numeric(cleaned_num, errors='coerce')
        if converted.notnull().sum() / total_valid > 0.85:
            return "numeric"
    except Exception:
        pass

    # 6. Text vs Categorical Check
    avg_words = sample_vals.str.split().str.len().mean()
    avg_char_len = sample_vals.str.len().mean()

    if avg_words > 4 or avg_char_len > 60:
        return "text"

    if unique_ratio < 0.8 or series.nunique() < 100:
        return "categorical"

    return "text"

