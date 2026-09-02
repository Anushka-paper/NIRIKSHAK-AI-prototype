import os
import pandas as pd
import numpy as np

def compute_vendor_features(df_master=None):
    """
    Computes 9 core vendor risk features (§7) using vectorized pandas aggregations.
    """
    print("[VENDOR FEATURES] Computing 9-dimensional Vendor Feature Store (§7)...")

    master_path = os.path.join("data", "integrated", "master", "unified_work_lifecycle.csv")
    if df_master is None and os.path.exists(master_path):
        df_master = pd.read_csv(master_path, low_memory=False)

    if df_master is None or df_master.empty:
        return pd.DataFrame()

    df_clean = df_master.copy()
    vendor_col = "canonical_vendor_name" if "canonical_vendor_name" in df_clean.columns else "vendor_name"
    df_clean["vendor"] = df_clean.get(vendor_col, pd.Series("", index=df_clean.index)).astype(str).str.strip().str.upper()

    # Filter invalid vendors
    df_valid = df_clean[(df_clean["vendor"] != "") & (df_clean["vendor"] != "UNKNOWN") & (df_clean["vendor"] != "NAN")].copy()

    amt_col = "sanctioned_amount_inr" if "sanctioned_amount_inr" in df_valid.columns else "recommended_amount_inr"
    df_valid["amount"] = pd.to_numeric(df_valid.get(amt_col, 0), errors="coerce").fillna(50000)
    df_valid["state"] = df_valid.get("canonical_state", pd.Series("UNKNOWN", index=df_valid.index)).astype(str)
    
    const_col = "constituency" if "constituency" in df_valid.columns else "canonical_mp_name"
    df_valid["constituency"] = df_valid.get(const_col, pd.Series("UNKNOWN", index=df_valid.index)).astype(str)
    
    work_id_col = "canonical_work_id" if "canonical_work_id" in df_valid.columns else "work_id"

    # Pre-compute constituency total spend
    const_spend = df_valid.groupby("constituency")["amount"].transform("sum")
    df_valid["const_spend"] = const_spend
    total_national_spend = df_valid["amount"].sum()

    # Fast vectorized aggregation
    grp = df_valid.groupby("vendor").agg(
        vendor_transaction_count=(work_id_col, "count"),
        vendor_total_value=("amount", "sum"),
        vendor_work_count=(work_id_col, "nunique"),
        vendor_constituency_count=("constituency", "nunique"),
        vendor_state_count=("state", "nunique"),
        amt_mean=("amount", "mean"),
        amt_std=("amount", "std"),
        max_const_spend=("const_spend", "max"),
        primary_constituency=("constituency", lambda s: s.mode()[0] if not s.empty else "UNKNOWN")
    ).reset_index()

    # 9 Features Derivation
    grp["canonical_vendor_name"] = grp["vendor"]
    grp["vendor_total_value_cr"] = (grp["vendor_total_value"] / 1e7).round(2)
    
    # Amount CV = std / mean
    grp["vendor_amount_cv"] = (grp["amt_std"].fillna(0) / grp["amt_mean"]).round(3)
    
    # Same day multi work proxy
    grp["same_day_multi_work_count"] = (grp["vendor_transaction_count"] - grp["vendor_work_count"]).clip(lower=0)

    # Vendor dependency = vendor spend / primary constituency spend
    grp["vendor_dependency"] = ((grp["vendor_total_value"] / grp["max_const_spend"].replace(0, np.nan)) * 100).fillna(100.0).round(1).clip(upper=100.0)

    # Vendor concentration pct = vendor spend / national spend
    grp["vendor_concentration_pct"] = ((grp["vendor_total_value"] / total_national_spend) * 1000).round(2)

    features = [
        "canonical_vendor_name", "vendor_transaction_count", "vendor_total_value",
        "vendor_total_value_cr", "vendor_work_count", "vendor_constituency_count",
        "vendor_state_count", "vendor_concentration_pct", "vendor_amount_cv",
        "same_day_multi_work_count", "vendor_dependency", "primary_constituency"
    ]

    df_res = grp[features].sort_values(by="vendor_total_value", ascending=False)
    print(f"[VENDOR FEATURES] Computed features for {len(df_res):,} valid vendor entities.")
    return df_res

def run_vendor_features_pipeline():
    df_feat = compute_vendor_features()
    if df_feat.empty:
        print("[VENDOR FEATURES] Master dataset empty.")
        return

    feat_dir = os.path.join("data", "features")
    os.makedirs(feat_dir, exist_ok=True)
    out_path = os.path.join(feat_dir, "features_vendor.csv")
    df_feat.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[NIRIKSHAK AI] Saved vendor feature store to {out_path}")

if __name__ == "__main__":
    run_vendor_features_pipeline()
