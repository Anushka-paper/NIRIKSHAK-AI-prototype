"""
Isolation Forest Evaluation Script for NIRIKSHAK-AI.
Calculates:
- ROC-AUC score
- Overall Accuracy
- Precision, Recall, F1
- Confusion Matrix
- Threshold breakdown (0.50 -> 0.90)
Usage:
    python ml-service/anomaly/evaluate.py --parliament lok_sabha
    python ml-service/anomaly/evaluate.py --parliament rajya_sabha
    python ml-service/anomaly/evaluate.py --parliament all
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    precision_score,
    recall_score,
    f1_score
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PRED_DIR = BASE_DIR / "data" / "predictions"
FEAT_DIR = BASE_DIR / "data" / "features"

def evaluate_house(parliament: str = "lok_sabha"):
    pred_file = PRED_DIR / parliament / "work_anomalies.csv"
    feat_file = FEAT_DIR / parliament / "canonical_work_features.csv"

    if not pred_file.exists() or not feat_file.exists():
        print(f"[-] Missing predictions or features for [{parliament}]. Please run training first.")
        return

    print("=" * 65)
    print(f"ISOLATION FOREST EVALUATION: {parliament.upper()}")
    print("=" * 65)

    df_pred = pd.read_csv(pred_file, low_memory=False)
    df_feat = pd.read_csv(feat_file, low_memory=False)

    cols = ["work_id", "is_overpayment", "budget_ceiling_breach_flag", "evidence_missing_flag"]
    available_cols = [c for c in cols if c in df_feat.columns]
    merged = df_pred.merge(df_feat[available_cols], on="work_id")

    # Domain Ground Truth Proxy Rules:
    # 1. Sanction cost > 300% above district-category median
    # 2. Overpayment (total expenditure > sanction amount)
    # 3. Budget ceiling breached
    # 4. Completed with missing evidence AND duration > 730 days
    y_true = (
        (merged.get("cost_deviation_pct", 0) > 300) |
        (merged.get("is_overpayment", False) == True) |
        (merged.get("budget_ceiling_breach_flag", False) == True) |
        ((merged.get("evidence_missing_flag", False) == True) & (merged.get("total_execution_days", 0) > 730))
    ).astype(int)

    y_pred = merged["is_anomaly"].astype(int)
    y_score = merged["anomaly_score"]

    total_works = len(merged)
    ground_truth_count = y_true.sum()
    pred_count = y_pred.sum()
    acc = accuracy_score(y_true, y_pred)
    roc_auc = roc_auc_score(y_true, y_score)
    cm = confusion_matrix(y_true, y_pred)

    print(f"\n1. DATASET OVERVIEW:")
    print(f"   Total Works Evaluated:           {total_works:,}")
    print(f"   Confirmed Ground-Truth Outliers: {ground_truth_count:,} ({ground_truth_count/total_works*100:.2f}%)")
    print(f"   Isolation Forest Flagged:        {pred_count:,} ({pred_count/total_works*100:.2f}%)")

    print(f"\n2. DISCRIMINATIVE POWER:")
    print(f"   Overall Accuracy:  {acc * 100:.2f}%")
    print(f"   ROC-AUC Score:     {roc_auc:.4f}  (>0.80 = Strong Discriminator)")

    print(f"\n3. CONFUSION MATRIX:")
    print(f"   True Negatives  (Clean correctly identified):   {cm[0][0]:,}")
    print(f"   False Positives (Normal flagged as anomaly):    {cm[0][1]:,}")
    print(f"   False Negatives (Irregularity missed):          {cm[1][0]:,}")
    print(f"   True Positives  (Irregularity caught):          {cm[1][1]:,}")

    print(f"\n4. CLASSIFICATION METRICS:")
    print(classification_report(y_true, y_pred, target_names=["Normal", "Anomaly"], digits=4))

    print("5. PERFORMANCE BY DECISION THRESHOLD:")
    print(f"   {'Threshold':<11} | {'Flagged':<8} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<8}")
    print("   " + "-" * 56)
    for t in [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90]:
        yp = (y_score >= t).astype(int)
        p = precision_score(y_true, yp, zero_division=0) * 100
        r = recall_score(y_true, yp, zero_division=0) * 100
        f = f1_score(y_true, yp, zero_division=0)
        flagged = yp.sum()
        print(f"   >= {t:.2f}      | {flagged:<8,d} | {p:<9.2f}% | {r:<9.2f}% | {f:.4f}")
    print("\n" + "=" * 65 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Isolation Forest Performance")
    parser.add_argument("--parliament", "-p", default="all", choices=["lok_sabha", "rajya_sabha", "all"])
    args = parser.parse_args()

    houses = ["lok_sabha", "rajya_sabha"] if args.parliament == "all" else [args.parliament]
    for h in houses:
        evaluate_house(h)
