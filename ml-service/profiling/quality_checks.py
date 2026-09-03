import pandas as pd

def classify_missingness(pct: float, thresholds: dict = None) -> str:
    """Classifies missingness percentage into explainable quality tiers."""
    t = thresholds or {"low": 5.0, "moderate": 20.0, "high": 50.0}
    if pct == 0:
        return "Complete"
    elif pct <= t["low"]:
        return "Low"
    elif pct <= t["moderate"]:
        return "Moderate"
    elif pct <= t["high"]:
        return "High"
    else:
        return "Very High"

def run_quality_checks(df: pd.DataFrame, thresholds: dict = None) -> dict:
    """
    Executes dataset-level and column-level missingness and duplication checks.
    """
    total_rows = len(df)
    total_cols = len(df.columns)

    if total_rows == 0:
        return {
            "total_rows": 0,
            "total_columns": total_cols,
            "duplicate_rows_count": 0,
            "duplicate_rows_pct": 0.0,
            "missingness_summary": {},
            "completeness_score": 100.0
        }

    # Dataset Duplicate Rows
    dup_rows = int(df.duplicated().sum())
    dup_pct = round((dup_rows / total_rows) * 100, 2)

    # Column Missingness
    missingness_summary = {}
    total_cells = total_rows * total_cols
    total_missing_cells = 0

    for col in df.columns:
        null_cnt = int(df[col].isnull().sum())
        total_missing_cells += null_cnt
        null_pct = round((null_cnt / total_rows) * 100, 2)
        tier = classify_missingness(null_pct, thresholds)
        non_null_cnt = total_rows - null_cnt
        uniq_cnt = int(df[col].nunique(dropna=True))

        missingness_summary[col] = {
            "non_null_count": non_null_cnt,
            "missing_count": null_cnt,
            "missing_percentage": null_pct,
            "missingness_classification": tier,
            "unique_count": uniq_cnt,
            "unique_percentage": round((uniq_cnt / (non_null_cnt or 1)) * 100, 2),
            "duplicate_count": non_null_cnt - uniq_cnt
        }

    completeness_score = round(100.0 - ((total_missing_cells / (total_cells or 1)) * 100), 2)

    return {
        "total_rows": total_rows,
        "total_columns": total_cols,
        "duplicate_rows_count": dup_rows,
        "duplicate_rows_pct": dup_pct,
        "missingness_summary": missingness_summary,
        "completeness_score": completeness_score
    }

