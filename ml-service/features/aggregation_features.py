"""
Aggregation Feature Generator for MP, Constituency, State, and Vendor levels.
Also generates standalone dimension feature tables.
"""

from typing import Dict, Tuple
import pandas as pd
import numpy as np

def compute_group_aggregations(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Computes summary dimension tables for:
    - MP Features
    - Constituency Features
    - State Features
    - Vendor Features
    """
    is_completed = (df["has_completion"] == 1).astype(int)
    sanc_amt = pd.to_numeric(df["sanctioned_amount"], errors="coerce").fillna(0.0)
    exp_amt = pd.to_numeric(df["expenditure_amount"], errors="coerce").fillna(0.0)

    # A. MP Level
    mp_agg = df.groupby(["parliament", "state", "mp_name"]).agg(
        work_count=("canonical_work_id", "count"),
        sanctioned_work_count=("has_sanction", "sum"),
        completed_work_count=("has_completion", "sum"),
        total_sanctioned_amount=("sanctioned_amount", "sum"),
        total_expenditure=("expenditure_amount", "sum"),
        avg_sanctioned_amount=("sanctioned_amount", "mean"),
    ).reset_index()
    mp_agg["completion_rate"] = np.where(
        mp_agg["work_count"] > 0,
        (mp_agg["completed_work_count"] / mp_agg["work_count"]).round(3),
        0.0
    )
    mp_agg["utilization_rate"] = np.where(
        mp_agg["total_sanctioned_amount"] > 0,
        (mp_agg["total_expenditure"] / mp_agg["total_sanctioned_amount"]).round(3),
        0.0
    )

    # B. Constituency Level
    const_agg = df.groupby(["parliament", "state", "constituency"]).agg(
        work_count=("canonical_work_id", "count"),
        sanctioned_work_count=("has_sanction", "sum"),
        completed_work_count=("has_completion", "sum"),
        total_sanctioned_amount=("sanctioned_amount", "sum"),
        total_expenditure=("expenditure_amount", "sum"),
    ).reset_index()
    const_agg["completion_rate"] = np.where(
        const_agg["work_count"] > 0,
        (const_agg["completed_work_count"] / const_agg["work_count"]).round(3),
        0.0
    )
    const_agg["utilization_rate"] = np.where(
        const_agg["total_sanctioned_amount"] > 0,
        (const_agg["total_expenditure"] / const_agg["total_sanctioned_amount"]).round(3),
        0.0
    )

    # C. State Level
    state_agg = df.groupby(["parliament", "state"]).agg(
        work_count=("canonical_work_id", "count"),
        sanctioned_work_count=("has_sanction", "sum"),
        completed_work_count=("has_completion", "sum"),
        total_sanctioned_amount=("sanctioned_amount", "sum"),
        total_expenditure=("expenditure_amount", "sum"),
    ).reset_index()
    state_agg["completion_rate"] = np.where(
        state_agg["work_count"] > 0,
        (state_agg["completed_work_count"] / state_agg["work_count"]).round(3),
        0.0
    )
    state_agg["utilization_rate"] = np.where(
        state_agg["total_sanctioned_amount"] > 0,
        (state_agg["total_expenditure"] / state_agg["total_sanctioned_amount"]).round(3),
        0.0
    )

    # D. Vendor Level (filter out null vendor names)
    valid_vendors = df[df["vendor_name"].notna() & (df["vendor_name"].astype(str).str.strip() != "")]
    if not valid_vendors.empty:
        vendor_agg = valid_vendors.groupby("vendor_name").agg(
            work_count=("canonical_work_id", "count"),
            completed_work_count=("has_completion", "sum"),
            total_expenditure=("expenditure_amount", "sum"),
            avg_work_amount=("expenditure_amount", "mean"),
            unique_mps=("mp_name", "nunique"),
            unique_states=("state", "nunique"),
            unique_constituencies=("constituency", "nunique"),
        ).reset_index()
        vendor_agg["completion_rate"] = np.where(
            vendor_agg["work_count"] > 0,
            (vendor_agg["completed_work_count"] / vendor_agg["work_count"]).round(3),
            0.0
        )
    else:
        vendor_agg = pd.DataFrame(columns=[
            "vendor_name", "work_count", "completed_work_count", "total_expenditure",
            "avg_work_amount", "unique_mps", "unique_states", "unique_constituencies", "completion_rate"
        ])

    return mp_agg, const_agg, state_agg, vendor_agg

