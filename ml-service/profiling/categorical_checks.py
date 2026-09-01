import pandas as pd

def detect_case_and_formatting_variations(series: pd.Series) -> list:
    """
    Detects possible formatting variations (e.g., Uttar Pradesh, uttar pradesh, UP, U.P.)
    by comparing normalized lowercase strings against raw distinct category names.
    """
    s_clean = series.dropna().astype(str)
    raw_uniques = s_clean.unique()

    norm_map = {}
    for raw_val in raw_uniques:
        clean = raw_val.strip()
        norm = clean.lower().replace('.', '').replace(' ', '')
        if norm not in norm_map:
            norm_map[norm] = []
        norm_map[norm].append(raw_val)

    possible_variations = []
    for norm, original_list in norm_map.items():
        if len(original_list) > 1:
            possible_variations.append({
                "normalized_group": norm,
                "variants_found": original_list
            })

    return possible_variations

def profile_categorical_column(series: pd.Series, col_name: str) -> dict:
    """Profiles a categorical column."""
    total_rows = len(series)
    non_null = series.dropna().astype(str).str.strip()
    missing_cnt = total_rows - len(non_null)

    if len(non_null) == 0:
        return {
            "column_name": col_name,
            "unique_values": 0,
            "missing_values": missing_cnt,
            "top_categories": {},
            "rare_categories_count": 0,
            "possible_category_variations": []
        }

    val_counts = non_null.value_counts()
    unique_cnt = len(val_counts)

    top_categories = val_counts.head(5).to_dict()
    rare_threshold = len(non_null) * 0.01
    rare_count = int((val_counts < rare_threshold).sum())
    variations = detect_case_and_formatting_variations(series)

    return {
        "column_name": col_name,
        "unique_values": unique_cnt,
        "missing_values": missing_cnt,
        "top_categories": top_categories,
        "rare_categories_count": rare_count,
        "possible_category_variations": variations
    }

def run_categorical_checks(df: pd.DataFrame, categorical_cols: list) -> dict:
    """Runs categorical profiling on all detected categorical columns."""
    profiles = {}
    for col in categorical_cols:
        if col in df.columns:
            profiles[col] = profile_categorical_column(df[col], col)
    return profiles
