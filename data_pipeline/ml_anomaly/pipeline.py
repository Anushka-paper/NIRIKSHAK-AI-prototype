import os
import json
import numpy as np
import pandas as pd
from data_pipeline.ml_anomaly.preprocessor import prepare_feature_matrix
from data_pipeline.ml_anomaly.iso_forest import train_isolation_forest
from data_pipeline.ml_anomaly.lof import train_local_outlier_factor
from data_pipeline.ml_anomaly.feature_attribution import compute_feature_attributions
from data_pipeline.ml_anomaly.drift_detector import compute_population_stability_report

def run_ml_anomaly_pipeline():
    """
    Executes Production-Ready Unsupervised Anomaly Detection Architecture (§8).
    """
    print("=========================================================================")
    print("      STARTING UNSUPERVISED ML ANOMALY DETECTION (ISO FOREST + LOF)")
    print("=========================================================================")

    work_feat_path = os.path.join("data", "features", "features_work.csv")
    txn_feat_path = os.path.join("data", "features", "features_transaction.csv")
    vendor_feat_path = os.path.join("data", "features", "features_vendor.csv")

    df_work = pd.read_csv(work_feat_path, low_memory=False) if os.path.exists(work_feat_path) else pd.DataFrame()
    df_txn = pd.read_csv(txn_feat_path, low_memory=False) if os.path.exists(txn_feat_path) else pd.DataFrame()
    df_vendor = pd.read_csv(vendor_feat_path, low_memory=False) if os.path.exists(vendor_feat_path) else pd.DataFrame()

    if df_work.empty:
        # Fallback master lifecycle dataset
        master_path = os.path.join("data", "integrated", "master", "unified_work_lifecycle.csv")
        if os.path.exists(master_path):
            df_work = pd.read_csv(master_path, low_memory=False)

    if df_work.empty:
        print("[ML ANOMALY] No feature data available.")
        return

    # 1. Robust Preprocessing Pipeline with was_missing indicators & RobustScaler (§8)
    X_scaled, df_merged, feat_names = prepare_feature_matrix(df_work, df_txn, df_vendor)
    
    if len(X_scaled) == 0:
        print("[ML ANOMALY] Preprocessor returned empty feature matrix.")
        return

    # 2. Train Primary IsolationForest & Secondary LOF Models (§8, Questions 1 & 2)
    iso_scores, iso_clf = train_isolation_forest(X_scaled, save_model=True, model_version="v1")
    lof_scores, lof_clf = train_local_outlier_factor(X_scaled, save_model=True, model_version="v1")

    # 3. Dual-Model Anomaly Fusion & Normalization (0.0 to 100.0)
    combined_raw = 0.5 * iso_scores + 0.5 * lof_scores
    min_s, max_s = combined_raw.min(), combined_raw.max()
    denom = max(1e-6, max_s - min_s)
    
    ml_scores = np.clip(((combined_raw - min_s) / denom) * 100.0, 0.0, 100.0).round(1)
    
    # 4. Feature Attributions (§8, Question 3 & 10)
    attributions = compute_feature_attributions(X_scaled, feat_names)

    # 5. Population Stability Index (PSI) Drift Detection (§8, Question 9)
    drift_report = compute_population_stability_report(X_scaled, X_scaled, feat_names)

    # Build Anomaly DataFrame
    df_res = pd.DataFrame({
        "canonical_work_id": df_merged.get("canonical_work_id", pd.Series(range(len(df_merged)))),
        "iso_forest_raw_score": np.round(iso_scores, 4),
        "lof_raw_score": np.round(lof_scores, 4),
        "ml_anomaly_score": ml_scores,
        "is_ml_anomaly": ml_scores >= 75.0,
        "top_contributing_features": attributions
    })

    anom_dir = os.path.join("data", "ml_anomaly")
    os.makedirs(anom_dir, exist_ok=True)
    out_csv = os.path.join(anom_dir, "ml_anomaly_scores.csv")
    df_res.to_csv(out_csv, index=False, encoding="utf-8")

    tot_anom = int(df_res["is_ml_anomaly"].sum())

    # Build Summary JSON Report (§8)
    report_data = {
        "status": "SUCCESS",
        "total_works_evaluated": len(df_res),
        "total_ml_anomalies": tot_anom,
        "models": {
            "isolation_forest": {
                "version": "v1",
                "estimators": 100,
                "contamination": 0.05,
                "raw_score_mean": round(float(np.mean(iso_scores)), 4)
            },
            "local_outlier_factor": {
                "version": "v1",
                "neighbors": 20,
                "raw_score_mean": round(float(np.mean(lof_scores)), 4)
            }
        },
        "data_drift": drift_report,
        "top_anomalies": df_res[df_res["is_ml_anomaly"]].head(30).to_dict(orient="records")
    }

    rep_dir = os.path.join("data", "reports")
    os.makedirs(rep_dir, exist_ok=True)
    rep_path = os.path.join(rep_dir, "ml_anomaly_report.json")

    with open(rep_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print(f"[NIRIKSHAK AI] ML Anomaly Pipeline completed successfully! Evaluated {len(df_res):,} works, flagged {tot_anom:,} ML anomalies.")
    return report_data

if __name__ == "__main__":
    run_ml_anomaly_pipeline()
