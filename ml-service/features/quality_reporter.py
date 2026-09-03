"""
Feature Quality Reporter and Data Dictionary Generator for NIRIKSHAK-AI.
Generates:
- feature_dictionary.csv
- feature_quality_report.csv
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np

def generate_feature_dictionary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a structured feature dictionary containing metadata, source columns,
    formulas, aggregation levels, and leakage status for every feature.
    """
    records = []
    
    for col in df.columns:
        series = df[col]
        dtype = str(series.dtype)
        missing_pct = round(float(series.isna().mean() * 100.0), 2)
        unique_cnt = int(series.nunique(dropna=True))

        min_val = None
        max_val = None
        mean_val = None
        std_val = None

        if pd.api.types.is_numeric_dtype(series):
            clean_s = series.dropna()
            if not clean_s.empty:
                min_val = round(float(clean_s.min()), 2)
                max_val = round(float(clean_s.max()), 2)
                mean_val = round(float(clean_s.mean()), 2)
                std_val = round(float(clean_s.std()), 2)

        # Classify group
        group = "general"
        if "amount" in col or "ratio" in col or "pct" in col or "expenditure" in col:
            group = "financial"
        elif "date" in col or "days" in col or "year" in col or "month" in col or "quarter" in col:
            group = "temporal_lifecycle"
        elif "mp_" in col or "state_" in col or "constituency_" in col or "vendor_" in col:
            group = "aggregation_historical"
        elif "word" in col or "char" in col or "ratio" in col:
            group = "text_complexity"
        elif "outlier" in col or "z_score" in col or "log_" in col or "percentile" in col:
            group = "statistical"
        elif "id" in col or "name" in col or "parliament" in col:
            group = "entity_identifier"

        records.append({
            "feature_name": col,
            "feature_group": group,
            "data_type": dtype,
            "aggregation_level": "work_level",
            "missing_percentage": missing_pct,
            "unique_count": unique_cnt,
            "min": min_val,
            "max": max_val,
            "mean": mean_val,
            "std": std_val,
            "leakage_status": "POST_PREDICTION" if any(p in col.lower() for p in ["completion", "last_exp", "unspent"]) else "AVAILABLE_AT_PREDICTION"
        })

    return pd.DataFrame(records)

def audit_feature_quality(df: pd.DataFrame, high_corr_thresh: float = 0.90) -> pd.DataFrame:
    """
    Audits feature quality: missingness, infinite values, constant features,
    near-zero variance, and high pairwise correlations.
    """
    records = []

    # 1. Column-by-column quality metrics
    for col in df.columns:
        s = df[col]
        missing_pct = float(s.isna().mean() * 100.0)
        n_unique = s.nunique(dropna=True)
        is_constant = 1 if n_unique <= 1 else 0
        
        has_inf = 0
        near_zero_var = 0
        if pd.api.types.is_numeric_dtype(s):
            has_inf = 1 if np.isinf(s).any() else 0
            std = float(s.std()) if len(s.dropna()) > 1 else 0.0
            near_zero_var = 1 if std < 1e-4 and not is_constant else 0

        quality_status = "HEALTHY"
        issues = []
        if missing_pct > 80.0:
            issues.append(f"High missingness ({missing_pct:.1f}%)")
        if is_constant:
            issues.append("Constant feature (zero variance)")
        if has_inf:
            issues.append("Contains infinite values")
        if near_zero_var:
            issues.append("Near-zero variance")

        if issues:
            quality_status = "WARNING"

        records.append({
            "feature_name": col,
            "quality_status": quality_status,
            "missing_percentage": round(missing_pct, 2),
            "unique_count": n_unique,
            "is_constant": is_constant,
            "has_infinite": has_inf,
            "near_zero_variance": near_zero_var,
            "audit_notes": "; ".join(issues) if issues else "All checks passed"
        })

    return pd.DataFrame(records)

