import os
import json
import numpy as np
import pandas as pd
from data_pipeline.ml_anomaly.preprocessor import prepare_feature_matrix
from data_pipeline.ml_anomaly.iso_forest import train_isolation_forest
from data_pipeline.ml_anomaly.lof import train_local_outlier_factor
from data_pipeline.ml_anomaly.feature_attribution import compute_feature_attributions

def run_ml_anomaly_pipeline():
    print("=========================================================================")
    print("      STARTING UNSUPERVISED ML ANOMALY DETECTION (ISO FOREST + LOF)")
    print("=========================================================================")

    work_feat_path = os.path.join("data", "features", "features_work.csv")
    txn_feat_path = os.path.join("data", "features", "features_transaction.csv")
    vendor_feat_path = os.path.join("data", "features", "features_vendor.csv")

    df_work = pd.read_csv(work_feat_path, low_memory=False) if os.path.exists(work_feat_path) else pd.DataFrame()
    df_txn = pd.read_csv(txn_feat_path, low_memory=False) if os.path.exists(txn_feat_path) else pd.DataFrame()
    df_vendor = pd.read_csv(vendor_feat_path, low_memory=False) if os.path.exists(vendor_feat_path) else pd.DataFrame()

    X_scaled, df_merged, feat_names = prepare_feature_matrix(df_work, df_txn, df_vendor)
    
    if len(X_scaled) == 0:
        print("[ML ANOMALY] No feature data available.")
        return

    # Train Isolation Forest & LOF
    iso_scores, iso_clf = train_isolation_forest(X_scaled)
    lof_scores, lof_clf = train_local_outlier_factor(X_scaled)

    # Normalize scores 0.0 to 100.0
    combined_raw = 0.5 * iso_scores + 0.5 * lof_scores
    min_s, max_s = combined_raw.min(), combined_raw.max()
    denom = max(1e-6, max_s - min_s)
    
    ml_scores = np.clip(((combined_raw - min_s) / denom) * 100.0, 0.0, 100.0)
    
    # Feature Attributions
    attributions = compute_feature_attributions(X_scaled, feat_names)

    df_res = pd.DataFrame({
        "canonical_work_id": df_merged["canonical_work_id"],
        "iso_forest_raw_score": np.round(iso_scores, 4),
        "lof_raw_score": np.round(lof_scores, 4),
        "ml_anomaly_score": np.round(ml_scores, 2),
        "is_ml_anomaly": ml_scores >= 75.0,
        "top_contributing_features": attributions
    })

    anom_dir = os.path.join("data", "ml_anomaly")
    os.makedirs(anom_dir, exist_ok=True)
    out_csv = os.path.join(anom_dir, "ml_anomaly_scores.csv")
    df_res.to_csv(out_csv, index=False, encoding="utf-8")

    tot_anom = int(df_res["is_ml_anomaly"].sum())

    rep_dir = os.path.join("data", "reports")
    os.makedirs(rep_dir, exist_ok=True)
    rep_path = os.path.join(rep_dir, "ml_anomaly_report.json")

    with open(rep_path, "w", encoding="utf-8") as f:
        json.dump({
            "status": "SUCCESS",
            "total_works_evaluated": len(df_res),
            "total_ml_anomalies": tot_anom,
            "isolation_forest_estimators": 100,
            "lof_neighbors": 20
        }, f, indent=2)

    print(f"[NIRIKSHAK AI] ML Anomaly Pipeline completed successfully! Flagged {tot_anom:,} ML anomalies.")

if __name__ == "__main__":
    run_ml_anomaly_pipeline()
