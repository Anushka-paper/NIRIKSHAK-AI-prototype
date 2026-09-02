import os
import json
import joblib
import numpy as np
import pandas as pd
from data_pipeline.predictive.targets import generate_target_labels
from data_pipeline.predictive.feature_builder import prepare_predictive_features
from data_pipeline.predictive.delay_model import train_delay_models
from data_pipeline.predictive.cost_model import train_cost_model
from data_pipeline.predictive.stagnation_model import train_stagnation_model
from data_pipeline.predictive.explainability import generate_risk_explanations

def run_predictive_pipeline():
    print("=========================================================================")
    print("      STARTING PREDICTIVE RISK & EARLY WARNING MODELING PIPELINE")
    print("=========================================================================")

    work_feat_path = os.path.join("data", "features", "features_work.csv")
    master_path = os.path.join("data", "integrated", "master", "unified_work_lifecycle.csv")

    df_work = pd.read_csv(work_feat_path, low_memory=False) if os.path.exists(work_feat_path) else pd.DataFrame()
    df_lifecycle = pd.read_csv(master_path, low_memory=False) if os.path.exists(master_path) else pd.DataFrame()

    if df_work.empty:
        print("[PREDICTIVE ENGINE] No feature work data found.")
        return

    # 1. Generate Supervised Target Labels
    df_target = generate_target_labels(df_work, df_lifecycle)

    # 2. Build Predictive Feature Matrix
    X_scaled, df_m, feat_names = prepare_predictive_features(df_target)

    # 3. Train Models
    # Subsample 15,000 training set for high efficiency
    if len(X_scaled) > 15000:
        np.random.seed(42)
        train_idx = np.random.choice(len(X_scaled), size=15000, replace=False)
    else:
        train_idx = np.arange(len(X_scaled))

    X_tr = X_scaled[train_idx]
    y_delay_tr = df_target["is_delayed"].iloc[train_idx].values
    y_reg_tr = df_target["expected_delay_days"].iloc[train_idx].values
    y_cost_tr = df_target["is_cost_overrun"].iloc[train_idx].values
    y_stag_tr = df_target["is_stagnant"].iloc[train_idx].values

    delay_p, delay_days_pred, delay_clf, delay_reg, delay_m = train_delay_models(X_tr, y_delay_tr, y_reg_tr, X_scaled)
    cost_p, cost_clf, cost_m = train_cost_model(X_tr, y_cost_tr, X_scaled)
    stag_p, stag_clf, stag_m = train_stagnation_model(X_tr, y_stag_tr, X_scaled)

    # 4. Composite Risk Score & Categories
    comp_risk = (0.45 * delay_p + 0.35 * stag_p + 0.20 * cost_p) * 100.0
    
    categories = []
    priorities = []
    for score in comp_risk:
        if score >= 75.0:
            categories.append("CRITICAL")
            priorities.append("CRITICAL")
        elif score >= 50.0:
            categories.append("HIGH")
            priorities.append("HIGH")
        elif score >= 25.0:
            categories.append("MEDIUM")
            priorities.append("MEDIUM")
        else:
            categories.append("LOW")
            priorities.append("LOW")

    # 5. Explanations
    explanations = generate_risk_explanations(df_m, delay_p, cost_p, stag_p)

    # 6. Save Risk Scores Table
    df_res = pd.DataFrame({
        "canonical_work_id": df_m["canonical_work_id"],
        "source_house": df_m.get("source_house", "LOK_SABHA"),
        "canonical_state": df_m.get("canonical_state", "UNKNOWN"),
        "canonical_mp_name": df_m.get("canonical_mp_name", "UNKNOWN"),
        "canonical_work_category": df_m.get("canonical_work_category", "OTHER_WORKS"),
        "project_risk_score": np.round(comp_risk, 1),
        "delay_probability": np.round(delay_p, 4),
        "cost_overrun_probability": np.round(cost_p, 4),
        "stagnation_probability": np.round(stag_p, 4),
        "expected_delay_days": np.round(delay_days_pred, 1),
        "risk_category": categories,
        "recommended_monitoring_priority": priorities,
        "top_contributing_factors": explanations
    })

    pred_dir = os.path.join("data", "predictive")
    os.makedirs(pred_dir, exist_ok=True)
    df_res.to_csv(os.path.join(pred_dir, "predictive_risk_scores.csv"), index=False, encoding="utf-8")

    # Save Models
    model_dir = os.path.join(pred_dir, "models")
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(delay_clf, os.path.join(model_dir, "delay_classifier.joblib"))
    joblib.dump(delay_reg, os.path.join(model_dir, "delay_regressor.joblib"))
    joblib.dump(cost_clf, os.path.join(model_dir, "cost_classifier.joblib"))
    joblib.dump(stag_clf, os.path.join(model_dir, "stagnation_classifier.joblib"))

    # Save Metrics Report
    rep_dir = os.path.join("data", "reports")
    os.makedirs(rep_dir, exist_ok=True)
    rep_path = os.path.join(rep_dir, "predictive_metrics_report.json")

    metrics_report = {
        "status": "SUCCESS",
        "total_works_evaluated": len(df_res),
        "high_risk_projects_count": int((df_res["project_risk_score"] >= 50.0).sum()),
        "critical_risk_projects_count": int((df_res["project_risk_score"] >= 75.0).sum()),
        "model_evaluation_metrics": {
            **delay_m,
            **cost_m,
            **stag_m
        }
    }

    with open(rep_path, "w", encoding="utf-8") as f:
        json.dump(metrics_report, f, indent=2)

    print(f"[NIRIKSHAK AI] Predictive Pipeline completed successfully! Report saved to {rep_path}")

if __name__ == "__main__":
    run_predictive_pipeline()
