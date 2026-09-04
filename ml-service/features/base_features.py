"""
Stage 4 — BASE FEATURE ENGINEERING (shared, computed once)
- cost_deviation_pct = (sanction_amount - district_category_median) / median
- recommendation_to_sanction_days, sanction_to_first_payment_days, last_payment_to_completion_days
- total_expenditure_vs_sanction_amount (overpayment/underpayment check)
- mp_recommended_total_vs_allocated_limit (budget-ceiling breach flag)
- evidence_missing_flag (from Completion's "Evidence/Image Indicator")
- vendor_txn_count_per_district_per_quarter
- Writes versioned feature store table keyed by work_id into data/features/{parliament}/canonical_work_features.csv
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Stage4-BaseFeatureEngineering")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FEATURE_DIR = BASE_DIR / "data" / "features"

def compute_base_features(
    canonical_tables: Dict[str, pd.DataFrame],
    parliament: str = "lok_sabha",
    features_base: Optional[Path] = None
) -> pd.DataFrame:
    """
    Computes schema-aligned base features and persists the canonical feature store.
    """
    out_dir = features_base or (FEATURE_DIR / parliament)
    out_dir.mkdir(parents=True, exist_ok=True)

    df_works = canonical_tables.get("Works", pd.DataFrame())
    df_rec = canonical_tables.get("Recommendations", pd.DataFrame())
    df_sanc = canonical_tables.get("Sanctions", pd.DataFrame())
    df_exp = canonical_tables.get("Expenditure", pd.DataFrame())
    df_comp = canonical_tables.get("Completion", pd.DataFrame())
    df_alloc = canonical_tables.get("MP_Allocation", pd.DataFrame())
    df_mps = canonical_tables.get("MPs", pd.DataFrame())

    if df_works.empty:
        logger.warning(f"[{parliament.upper()}] Works table is empty; skipping base feature engineering.")
        return pd.DataFrame()

    # Anchor table: Works
    features = df_works[["work_id", "work_id_raw", "category", "description", "mp_id", "constituency_id", "ida_id", "state", "parliament"]].copy()

    # Join Recommendations
    if not df_rec.empty:
        features = features.merge(
            df_rec[["work_id", "recommendation_date", "recommended_amount"]],
            on="work_id", how="left"
        )
    else:
        features["recommendation_date"] = None
        features["recommended_amount"] = 0.0

    # Join Sanctions
    if not df_sanc.empty:
        features = features.merge(
            df_sanc[["work_id", "sanction_date", "sanction_amount", "status"]],
            on="work_id", how="left"
        )
    else:
        features["sanction_date"] = None
        features["sanction_amount"] = 0.0
        features["status"] = "UNKNOWN"

    # Join Completion
    if not df_comp.empty:
        features = features.merge(
            df_comp[["work_id", "completion_date", "disbursed_amount", "has_evidence"]],
            on="work_id", how="left"
        )
    else:
        features["completion_date"] = None
        features["disbursed_amount"] = 0.0
        features["has_evidence"] = False

    # Aggregate Expenditure per work_id
    if not df_exp.empty:
        exp_agg = df_exp.groupby("work_id").agg(
            total_expenditure=("amount", "sum"),
            expenditure_tx_count=("txn_id", "count"),
            first_payment_date=("txn_date", "min"),
            last_payment_date=("txn_date", "max"),
            unique_vendors=("vendor_id", "nunique")
        ).reset_index()
        features = features.merge(exp_agg, on="work_id", how="left")
    else:
        features["total_expenditure"] = 0.0
        features["expenditure_tx_count"] = 0
        features["first_payment_date"] = None
        features["last_payment_date"] = None
        features["unique_vendors"] = 0

    features["total_expenditure"] = features["total_expenditure"].fillna(0.0)
    features["expenditure_tx_count"] = features["expenditure_tx_count"].fillna(0).astype(int)
    features["unique_vendors"] = features["unique_vendors"].fillna(0).astype(int)

    # 1. Feature: cost_deviation_pct = (sanction_amount - district_category_median) / median
    # Calculate median by state + category
    cat_medians = features.groupby(["state", "category"])["sanction_amount"].transform("median")
    features["district_category_median"] = cat_medians.fillna(features["sanction_amount"].median()).fillna(500000.0)
    
    # Avoid zero-division
    denom = features["district_category_median"].replace(0, 500000.0)
    features["cost_deviation_pct"] = round(
        ((features["sanction_amount"].fillna(0.0) - features["district_category_median"]) / denom) * 100.0, 2
    )

    # 2. Lifecycle Duration Features
    rec_dt = pd.to_datetime(features["recommendation_date"], errors="coerce")
    sanc_dt = pd.to_datetime(features["sanction_date"], errors="coerce")
    first_pay_dt = pd.to_datetime(features["first_payment_date"], errors="coerce")
    last_pay_dt = pd.to_datetime(features["last_payment_date"], errors="coerce")
    comp_dt = pd.to_datetime(features["completion_date"], errors="coerce")

    features["recommendation_to_sanction_days"] = (sanc_dt - rec_dt).dt.days.fillna(-1).astype(int)
    features["sanction_to_first_payment_days"] = (first_pay_dt - sanc_dt).dt.days.fillna(-1).astype(int)
    features["last_payment_to_completion_days"] = (comp_dt - last_pay_dt).dt.days.fillna(-1).astype(int)
    features["total_execution_days"] = (comp_dt - sanc_dt).dt.days.fillna(-1).astype(int)

    # 3. Feature: total_expenditure_vs_sanction_amount (Overpayment / Underpayment Ratio)
    sanc_safe = features["sanction_amount"].replace(0, np.nan)
    features["total_expenditure_vs_sanction_amount"] = round((features["total_expenditure"] / sanc_safe).fillna(0.0), 4)
    features["is_overpayment"] = features["total_expenditure"] > features["sanction_amount"].fillna(0.0)

    # 4. Feature: mp_recommended_total_vs_allocated_limit (Budget Ceiling Breach Flag)
    if not df_alloc.empty:
        mp_alloc_map = df_alloc.set_index("mp_id")["allocated_amount"].to_dict()
    else:
        mp_alloc_map = {}

    mp_rec_totals = features.groupby("mp_id")["recommended_amount"].transform("sum")
    features["mp_total_recommended"] = mp_rec_totals
    features["mp_allocated_limit"] = features["mp_id"].map(mp_alloc_map).fillna(500000000.0) # Default 50 Cr ceiling
    features["mp_recommended_total_vs_allocated_limit"] = round(
        (features["mp_total_recommended"] / features["mp_allocated_limit"]).fillna(0.0), 4
    )
    features["budget_ceiling_breach_flag"] = features["mp_total_recommended"] > features["mp_allocated_limit"]

    # 5. Feature: evidence_missing_flag
    # Completed works with no photo/evidence flag
    is_completed = features["completion_date"].notna() | (features["status"].astype(str).str.upper() == "COMPLETED")
    features["evidence_missing_flag"] = is_completed & (~features["has_evidence"].fillna(False))

    # 6. Feature: vendor_txn_count_per_district_per_quarter
    if not df_exp.empty and "vendor_id" in df_exp.columns and "txn_date" in df_exp.columns:
        df_exp_copy = df_exp.copy()
        df_exp_copy["dt"] = pd.to_datetime(df_exp_copy["txn_date"], errors="coerce")
        df_exp_copy["quarter"] = df_exp_copy["dt"].dt.to_period("Q").astype(str)
        vend_counts = df_exp_copy.groupby(["vendor_id", "state", "quarter"])["txn_id"].transform("count")
        df_exp_copy["vendor_qtr_density"] = vend_counts
        
        # Max vendor density mapped back to work
        work_vend_density = df_exp_copy.groupby("work_id")["vendor_qtr_density"].max().to_dict()
        features["vendor_txn_count_per_district_per_quarter"] = features["work_id"].map(work_vend_density).fillna(0).astype(int)
    else:
        features["vendor_txn_count_per_district_per_quarter"] = 0

    # 7. Write to Versioned Feature Store
    feature_store_file = out_dir / "canonical_work_features.csv"
    features.to_csv(feature_store_file, index=False)
    logger.info(f"[{parliament.upper()}] Written Canonical Feature Store ({len(features)} rows, {len(features.columns)} features) -> {feature_store_file.name}")

    return features
