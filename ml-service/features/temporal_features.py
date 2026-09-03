"""
Temporal, Lifecycle Duration, and Chronology Features for NIRIKSHAK-AI.
Uses Indian Financial Year (April - March) standard.
"""

import pandas as pd
import numpy as np

def to_financial_year(dt_series: pd.Series) -> pd.Series:
    """
    Computes Indian Financial Year (e.g., '2024-2025' for date in April 2024 to March 2025).
    """
    dt = pd.to_datetime(dt_series, errors="coerce")
    fy = []
    for d in dt:
        if pd.isna(d):
            fy.append(None)
        else:
            year = d.year
            if d.month >= 4:
                fy.append(f"{year}-{year+1}")
            else:
                fy.append(f"{year-1}-{year}")
    return pd.Series(fy, index=dt_series.index)

def compute_temporal_and_lifecycle_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates temporal components, lifecycle durations, and chronology flags.
    """
    df = df.copy()

    rec_dt = pd.to_datetime(df.get("recommended_date"), errors="coerce")
    sanc_dt = pd.to_datetime(df.get("sanction_date"), errors="coerce")
    first_exp_dt = pd.to_datetime(df.get("first_expenditure_date"), errors="coerce")
    last_exp_dt = pd.to_datetime(df.get("last_expenditure_date"), errors="coerce")
    comp_dt = pd.to_datetime(df.get("completion_date"), errors="coerce")

    # 1. Temporal breakdown for Sanction Date (primary milestone)
    df["sanction_year"] = sanc_dt.dt.year
    df["sanction_month"] = sanc_dt.dt.month
    df["sanction_quarter"] = sanc_dt.dt.quarter
    df["sanction_financial_year"] = to_financial_year(sanc_dt)
    df["sanction_day_of_week"] = sanc_dt.dt.dayofweek

    # Recommendation breakdown
    df["recommendation_year"] = rec_dt.dt.year
    df["recommendation_month"] = rec_dt.dt.month
    df["recommendation_quarter"] = rec_dt.dt.quarter

    # Completion breakdown
    df["completion_year"] = comp_dt.dt.year
    df["completion_month"] = comp_dt.dt.month
    df["completion_quarter"] = comp_dt.dt.quarter

    # 2. Lifecycle Durations (Days)
    # Safe days calculation: (date2 - date1).dt.days, clipped or null
    def safe_days(dt2, dt1):
        diff = (dt2 - dt1).dt.days
        return diff

    df["recommendation_to_sanction_days"] = safe_days(sanc_dt, rec_dt)
    df["sanction_to_first_expenditure_days"] = safe_days(first_exp_dt, sanc_dt)
    df["sanction_to_last_expenditure_days"] = safe_days(last_exp_dt, sanc_dt)
    df["sanction_to_completion_days"] = safe_days(comp_dt, sanc_dt)
    df["first_expenditure_to_completion_days"] = safe_days(comp_dt, first_exp_dt)
    df["recommendation_to_completion_days"] = safe_days(comp_dt, rec_dt)
    df["expenditure_span_days"] = safe_days(last_exp_dt, first_exp_dt).fillna(0).clip(lower=0)
    df["total_execution_days"] = df["sanction_to_completion_days"]

    # 3. Lifecycle Chronology Checks
    df["recommendation_before_sanction"] = (rec_dt <= sanc_dt).astype(int)
    df["sanction_before_expenditure"] = (sanc_dt <= first_exp_dt).astype(int)
    df["expenditure_before_completion"] = (last_exp_dt <= comp_dt).astype(int)
    df["sanction_before_completion"] = (sanc_dt <= comp_dt).astype(int)

    # Chronology Anomaly Flags
    df["recommendation_sanction_chronology_issue"] = ((rec_dt.notna()) & (sanc_dt.notna()) & (rec_dt > sanc_dt)).astype(int)
    df["sanction_expenditure_chronology_issue"] = ((sanc_dt.notna()) & (first_exp_dt.notna()) & (sanc_dt > first_exp_dt)).astype(int)
    df["sanction_completion_chronology_issue"] = ((sanc_dt.notna()) & (comp_dt.notna()) & (sanc_dt > comp_dt)).astype(int)
    df["expenditure_completion_chronology_issue"] = ((last_exp_dt.notna()) & (comp_dt.notna()) & (last_exp_dt > comp_dt)).astype(int)

    df["valid_lifecycle_sequence"] = (
        (df["recommendation_sanction_chronology_issue"] == 0) &
        (df["sanction_expenditure_chronology_issue"] == 0) &
        (df["sanction_completion_chronology_issue"] == 0) &
        (df["expenditure_completion_chronology_issue"] == 0)
    ).astype(int)

    # 4. Lifecycle Stages Count & Categorical Status
    has_r = df["has_recommendation"]
    has_s = df["has_sanction"]
    has_e = df["has_expenditure"]
    has_c = df["has_completion"]

    df["lifecycle_stage_count"] = has_r + has_s + has_e + has_c
    df["lifecycle_completion_percentage"] = (df["lifecycle_stage_count"] / 4.0) * 100.0
    df["lifecycle_missing_stage_count"] = 4 - df["lifecycle_stage_count"]

    # Assign categorical lifecycle_status
    status_series = []
    for _, r in df.iterrows():
        if r["has_completion"] == 1:
            status_series.append("COMPLETED")
        elif r["has_expenditure"] == 1:
            status_series.append("EXPENDITURE_STARTED")
        elif r["has_sanction"] == 1:
            status_series.append("SANCTIONED")
        elif r["has_recommendation"] == 1:
            status_series.append("RECOMMENDED_ONLY")
        else:
            status_series.append("UNKNOWN")
    df["lifecycle_status"] = status_series

    return df

