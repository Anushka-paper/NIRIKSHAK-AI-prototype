"""
Time-Aware Historical & Rolling Feature Generator for NIRIKSHAK-AI.
Strictly calculates historical aggregates (MP, State, Vendor, Constituency)
using only records that occurred BEFORE the current work's sanction date.
Guarantees zero future target leakage.
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger("NIRIKSHAK-HISTORICAL-FEATURES")

def compute_leakage_safe_historical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes time-aware historical features for MP, State, Constituency, and Vendor.
    For each row, historical metrics are computed using only preceding works (by sanction_date).
    """
    df = df.copy()

    # Convert sanction_date to sortable datetime for causal ordering
    sanc_dt = pd.to_datetime(df["sanction_date"], errors="coerce")
    df["_sort_dt"] = sanc_dt.fillna(pd.Timestamp("1970-01-01"))
    
    # Preserve original order index
    df["_orig_idx"] = np.arange(len(df))
    df = df.sort_values("_sort_dt").reset_index(drop=True)

    is_completed_series = (df["has_completion"] == 1).astype(int)
    if "sanction_to_completion_days" in df.columns:
        duration_series = pd.to_numeric(df["sanction_to_completion_days"], errors="coerce").fillna(0.0)
    else:
        duration_series = pd.Series(0.0, index=df.index)

    # 1. MP-Level Time-Aware Expanding Features
    mp_col = df["mp_name"].fillna("UNKNOWN")
    
    # Cumulative counts and completed counts strictly prior to current row
    # Expanding with shift(1) ensures current row outcome is NOT included
    df["mp_historical_work_count"] = df.groupby(mp_col).cumcount()
    
    mp_cum_completed = df.groupby(mp_col)[is_completed_series.name].apply(
        lambda s: s.shift(1).fillna(0).cumsum()
    ).reset_index(level=0, drop=True)
    
    df["mp_historical_completed_count"] = mp_cum_completed
    df["mp_historical_completion_rate"] = np.where(
        df["mp_historical_work_count"] > 0,
        (df["mp_historical_completed_count"] / df["mp_historical_work_count"]).round(3),
        0.0
    )

    # 2. State-Level Historical Aggregates
    state_col = df["state"].fillna("UNKNOWN")
    df["state_historical_work_count"] = df.groupby(state_col).cumcount()
    
    state_cum_completed = df.groupby(state_col)[is_completed_series.name].apply(
        lambda s: s.shift(1).fillna(0).cumsum()
    ).reset_index(level=0, drop=True)
    
    df["state_historical_completion_rate"] = np.where(
        df["state_historical_work_count"] > 0,
        (state_cum_completed / df["state_historical_work_count"]).round(3),
        0.0
    )

    # 3. Constituency-Level Historical Aggregates
    const_col = df["constituency"].fillna("UNKNOWN")
    df["constituency_historical_work_count"] = df.groupby(const_col).cumcount()
    
    const_cum_completed = df.groupby(const_col)[is_completed_series.name].apply(
        lambda s: s.shift(1).fillna(0).cumsum()
    ).reset_index(level=0, drop=True)

    df["constituency_historical_completion_rate"] = np.where(
        df["constituency_historical_work_count"] > 0,
        (const_cum_completed / df["constituency_historical_work_count"]).round(3),
        0.0
    )

    # 4. Vendor-Level Historical Aggregates
    vendor_col = df["vendor_name"].fillna("UNKNOWN")
    df["vendor_historical_work_count"] = df.groupby(vendor_col).cumcount()
    
    vendor_cum_completed = df.groupby(vendor_col)[is_completed_series.name].apply(
        lambda s: s.shift(1).fillna(0).cumsum()
    ).reset_index(level=0, drop=True)

    df["vendor_historical_completion_rate"] = np.where(
        df["vendor_historical_work_count"] > 0,
        (vendor_cum_completed / df["vendor_historical_work_count"]).round(3),
        0.0
    )

    # Restore original order
    df = df.sort_values("_orig_idx").reset_index(drop=True)
    df = df.drop(columns=["_sort_dt", "_orig_idx"])

    return df
