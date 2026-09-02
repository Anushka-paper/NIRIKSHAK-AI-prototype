import numpy as np
import pandas as pd
from data_pipeline.features.config import FEATURE_VERSION

def compute_vendor_features(df_vendor_master, df_exp, df_lifecycle):
    if df_vendor_master.empty:
        return pd.DataFrame()
    print(f"[FEATURE STORE] Computing features_vendor for {len(df_vendor_master):,} vendors...")
    
    df_v = df_vendor_master.copy()
    if "vendor_id" not in df_v.columns:
        df_v["vendor_id"] = [f"VENDOR_{i+1:06d}" for i in range(len(df_v))]

    if not df_exp.empty and "canonical_vendor_name" in df_exp.columns:
        life_cols = [c for c in ["canonical_work_id", "canonical_constituency", "canonical_mp_name"] if c in df_lifecycle.columns]
        exp_merged = df_exp.merge(df_lifecycle[life_cols], on="canonical_work_id", how="left") if not df_lifecycle.empty else df_exp.copy()
        
        agg_kwargs = {"work_count": ("canonical_work_id", "nunique")}
        if "canonical_constituency" in exp_merged.columns:
            agg_kwargs["constituency_count"] = ("canonical_constituency", "nunique")
        if "canonical_mp_name" in exp_merged.columns:
            agg_kwargs["mp_count"] = ("canonical_mp_name", "nunique")
        if "expenditure_amount_inr" in exp_merged.columns:
            agg_kwargs["total_expenditure_inr"] = ("expenditure_amount_inr", "sum")
            
        v_agg = exp_merged.groupby("canonical_vendor_name").agg(**agg_kwargs).reset_index()
        
        if "canonical_mp_name" in exp_merged.columns and "expenditure_amount_inr" in exp_merged.columns:
            mp_group = exp_merged.groupby(["canonical_vendor_name", "canonical_mp_name"])["expenditure_amount_inr"].sum().reset_index()
            tot_group = exp_merged.groupby("canonical_vendor_name")["expenditure_amount_inr"].sum().reset_index().rename(columns={"expenditure_amount_inr": "tot_exp"})
            merged_dep = mp_group.merge(tot_group, on="canonical_vendor_name")
            merged_dep["dep_pct"] = np.where(merged_dep["tot_exp"] > 0, (merged_dep["expenditure_amount_inr"] / merged_dep["tot_exp"]) * 100.0, 0.0)
            max_dep = merged_dep.groupby("canonical_vendor_name")["dep_pct"].max().reset_index().rename(columns={"dep_pct": "single_mp_dependence_pct"})
            v_agg = v_agg.merge(max_dep, on="canonical_vendor_name", how="left")
        else:
            v_agg["single_mp_dependence_pct"] = 100.0

        df_v = df_v.merge(v_agg, left_on="canonical_name", right_on="canonical_vendor_name", how="left")

    df_v["work_count"] = df_v.get("work_count", pd.Series(1, index=df_v.index)).fillna(1).astype(int)
    df_v["constituency_count"] = df_v.get("constituency_count", pd.Series(1, index=df_v.index)).fillna(1).astype(int)
    df_v["mp_count"] = df_v.get("mp_count", pd.Series(1, index=df_v.index)).fillna(1).astype(int)
    df_v["total_expenditure_inr"] = df_v.get("total_expenditure_inr_y", df_v.get("total_expenditure_inr", pd.Series(0.0, index=df_v.index))).fillna(0.0)
    df_v["avg_work_value_inr"] = np.where(df_v["work_count"] > 0, df_v["total_expenditure_inr"] / df_v["work_count"], 0.0)
    df_v["single_mp_dependence_pct"] = df_v.get("single_mp_dependence_pct", pd.Series(100.0, index=df_v.index)).fillna(100.0)
    tot_works = max(1, df_v["work_count"].sum())
    df_v["concentration_pct"] = np.minimum(100.0, round((df_v["work_count"] / tot_works) * 100.0 * 50.0, 2))

    df_v["feature_version"] = FEATURE_VERSION
    df_v["computed_at"] = pd.Timestamp.now().isoformat()
    
    keep_cols = [
        "vendor_id", "canonical_name", "canonical_state", "work_count", "constituency_count",
        "mp_count", "total_expenditure_inr", "avg_work_value_inr", "single_mp_dependence_pct",
        "concentration_pct", "feature_version", "computed_at"
    ]
    res_cols = [c for c in keep_cols if c in df_v.columns]
    return df_v[res_cols]
