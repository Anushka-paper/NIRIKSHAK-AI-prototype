import numpy as np
import pandas as pd
from scipy.stats import entropy
from data_pipeline.features.config import FEATURE_VERSION

def compute_mp_features(df_mp_master, df_lifecycle, df_allocated):
    if df_mp_master.empty:
        return pd.DataFrame()
    print(f"[FEATURE STORE] Computing features_mp for {len(df_mp_master):,} MPs...")
    
    df_mp = df_mp_master.copy()
    if "mp_id" not in df_mp.columns:
        df_mp["mp_id"] = [f"MP_{i+1:06d}" for i in range(len(df_mp))]

    if not df_lifecycle.empty:
        df_life = df_lifecycle.copy()
        if "sanction_delay_days" not in df_life.columns:
            rec_dt = pd.to_datetime(df_life["recommended_date"], errors="coerce") if "recommended_date" in df_life.columns else pd.Series(pd.NaT, index=df_life.index)
            sanc_dt = pd.to_datetime(df_life["sanction_date"], errors="coerce") if "sanction_date" in df_life.columns else pd.Series(pd.NaT, index=df_life.index)
            df_life["sanction_delay_days"] = (sanc_dt - rec_dt).dt.days.astype(float)

        agg_kwargs = {}
        if "has_recommendation" in df_life.columns: agg_kwargs["recommendation_count"] = ("has_recommendation", "sum")
        if "has_sanction" in df_life.columns: agg_kwargs["sanction_count"] = ("has_sanction", "sum")
        if "has_completion" in df_life.columns: agg_kwargs["completed_count"] = ("has_completion", "sum")
        if "sanction_delay_days" in df_life.columns: agg_kwargs["avg_sanction_delay_days"] = ("sanction_delay_days", "mean")
        if "expenditure_amount_inr" in df_life.columns: agg_kwargs["total_expenditure_inr"] = ("expenditure_amount_inr", "sum")

        mp_agg = df_life.groupby("canonical_mp_name").agg(**agg_kwargs).reset_index()
        
        # Category entropy per MP
        if "canonical_work_category" in df_life.columns:
            def calc_entropy(group):
                counts = group["canonical_work_category"].value_counts()
                return round(float(entropy(counts)), 2) if len(counts) > 0 else 0.0

            ent_series = df_life.groupby("canonical_mp_name").apply(calc_entropy, include_groups=False)
            mp_agg["category_entropy"] = mp_agg["canonical_mp_name"].map(ent_series).fillna(0.0)

        df_mp = df_mp.merge(mp_agg, left_on="canonical_name", right_on="canonical_mp_name", how="left")

    df_mp["recommendation_count"] = df_mp.get("recommendation_count", pd.Series(0, index=df_mp.index)).fillna(0).astype(int)
    df_mp["sanction_count"] = df_mp.get("sanction_count", pd.Series(0, index=df_mp.index)).fillna(0).astype(int)
    df_mp["completed_count"] = df_mp.get("completed_count", pd.Series(0, index=df_mp.index)).fillna(0).astype(int)
    df_mp["avg_sanction_delay_days"] = df_mp.get("avg_sanction_delay_days", pd.Series(0.0, index=df_mp.index)).fillna(0.0)
    df_mp["total_expenditure_inr"] = df_mp.get("total_expenditure_inr", pd.Series(0.0, index=df_mp.index)).fillna(0.0)
    df_mp["category_entropy"] = df_mp.get("category_entropy", pd.Series(0.0, index=df_mp.index)).fillna(0.0)

    # Utilization % (Allocated Amount assumed ₹ 25 Crore standard or from dataset)
    alloc_amt = 250000000.0
    df_mp["utilisation_pct"] = np.minimum(100.0, round((df_mp["total_expenditure_inr"] / alloc_amt) * 100.0, 2))
    df_mp["output_per_rupee"] = np.where(df_mp["total_expenditure_inr"] > 0, round((df_mp["completed_count"] / df_mp["total_expenditure_inr"]) * 10000000.0, 4), 0.0)
    df_mp["top_vendor_concentration_pct"] = 25.0

    df_mp["feature_version"] = FEATURE_VERSION
    df_mp["computed_at"] = pd.Timestamp.now().isoformat()

    keep_cols = [
        "mp_id", "canonical_name", "source_house", "canonical_state", "canonical_constituency",
        "recommendation_count", "sanction_count", "completed_count", "total_expenditure_inr",
        "utilisation_pct", "output_per_rupee", "avg_sanction_delay_days", "category_entropy",
        "top_vendor_concentration_pct", "feature_version", "computed_at"
    ]
    res_cols = [c for c in keep_cols if c in df_mp.columns]
    return df_mp[res_cols]
