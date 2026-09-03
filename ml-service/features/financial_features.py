"""
Financial Features and Gap Metrics for NIRIKSHAK-AI.
Implements safe division, differences, percentage changes, and utilization metrics.
"""

import pandas as pd
import numpy as np

def safe_divide(numerator: pd.Series, denominator: pd.Series, fill_value: float = 0.0) -> pd.Series:
    """
    Safely divides two series, returning fill_value when denominator is zero, null, or invalid.
    """
    num = pd.to_numeric(numerator, errors="coerce")
    den = pd.to_numeric(denominator, errors="coerce")
    result = num / den
    result = result.replace([np.inf, -np.inf], np.nan)
    return result.fillna(fill_value)

def compute_financial_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates all financial differences, ratios, percentages, and financial gap features.
    """
    df = df.copy()

    rec_amt = pd.to_numeric(df.get("recommended_amount", np.nan), errors="coerce")
    sanc_amt = pd.to_numeric(df.get("sanctioned_amount", np.nan), errors="coerce")
    exp_amt = pd.to_numeric(df.get("expenditure_amount", 0.0), errors="coerce").fillna(0.0)
    comp_amt = pd.to_numeric(df.get("completion_amount", np.nan), errors="coerce")

    # 1. Differences
    df["recommendation_sanction_amount_difference"] = sanc_amt - rec_amt
    df["sanction_expenditure_amount_difference"] = sanc_amt - exp_amt
    df["sanction_completion_amount_difference"] = sanc_amt - comp_amt
    df["recommended_expenditure_difference"] = rec_amt - exp_amt

    # 2. Percentage changes (safe division)
    df["recommendation_to_sanction_amount_change_pct"] = safe_divide(
        sanc_amt - rec_amt, rec_amt
    ) * 100.0

    df["sanction_to_expenditure_amount_change_pct"] = safe_divide(
        exp_amt - sanc_amt, sanc_amt
    ) * 100.0

    df["sanction_to_completion_amount_change_pct"] = safe_divide(
        comp_amt - sanc_amt, sanc_amt
    ) * 100.0

    # 3. Utilization and Ratios
    df["expenditure_to_sanction_ratio"] = safe_divide(exp_amt, sanc_amt)
    df["expenditure_utilization_percentage"] = df["expenditure_to_sanction_ratio"] * 100.0
    df["completion_to_sanction_ratio"] = safe_divide(comp_amt, sanc_amt)
    df["completion_amount_percentage"] = df["completion_to_sanction_ratio"] * 100.0
    df["recommended_to_sanction_ratio"] = safe_divide(rec_amt, sanc_amt)

    # 4. Financial Gaps
    df["unspent_amount"] = (sanc_amt - exp_amt).clip(lower=0.0)
    df["remaining_sanctioned_amount"] = sanc_amt - exp_amt
    df["expenditure_gap"] = (sanc_amt - exp_amt).clip(lower=0.0)
    df["completion_financial_gap"] = (sanc_amt - comp_amt).clip(lower=0.0)

    # 5. Financial Consistency Flags
    df["expenditure_exceeds_sanction_flag"] = (exp_amt > (sanc_amt * 1.05)).astype(int) # 5% margin
    df["negative_expenditure_flag"] = (exp_amt < 0.0).astype(int)
    df["negative_sanction_flag"] = (sanc_amt < 0.0).astype(int)
    df["zero_sanction_flag"] = (sanc_amt == 0.0).astype(int)
    df["zero_expenditure_flag"] = (exp_amt == 0.0).astype(int)
    
    # Large amount change (> 25%)
    df["large_amount_change_flag"] = (
        df["recommendation_to_sanction_amount_change_pct"].abs() > 25.0
    ).astype(int)

    df["unusually_high_expenditure_ratio"] = (
        df["expenditure_to_sanction_ratio"] > 1.25
    ).astype(int)

    return df

