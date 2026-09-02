import os
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from data_pipeline.ml_anomaly.config import ISO_ESTIMATORS, ISO_CONTAMINATION, RANDOM_STATE

def train_isolation_forest(X, save_model=True, model_version="v1"):
    """
    Trains IsolationForest primary anomaly model with versioned artifact persistence (§8).
    """
    if len(X) == 0:
        return np.array([]), None

    print(f"[ML ANOMALY] Training Primary IsolationForest (estimators={ISO_ESTIMATORS}, contamination={ISO_CONTAMINATION}) on {len(X):,} samples...")
    clf = IsolationForest(
        n_estimators=ISO_ESTIMATORS,
        contamination=ISO_CONTAMINATION,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
    clf.fit(X)

    # Invert decision function so higher score = more anomalous
    raw_scores = -1.0 * clf.decision_function(X)

    if save_model:
        model_dir = os.path.join("data", "ml_anomaly", "models")
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, f"isolation_forest_{model_version}.joblib")
        joblib.dump(clf, model_path)
        print(f"[ML ANOMALY] Saved versioned IsolationForest model to {model_path}")

    return raw_scores, clf
