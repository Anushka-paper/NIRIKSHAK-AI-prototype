import os
import joblib
import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from data_pipeline.ml_anomaly.config import LOF_NEIGHBORS

def train_local_outlier_factor(X, save_model=True, model_version="v1"):
    """
    Trains Local Outlier Factor (LOF) secondary cross-check model with chunked batch evaluation (§8).
    """
    if len(X) == 0:
        return np.array([]), None

    n_neighbors = min(LOF_NEIGHBORS, max(2, len(X) - 1))
    print(f"[ML ANOMALY] Training Secondary Local Outlier Factor (LOF) (k={n_neighbors}) on {len(X):,} samples...")

    lof = LocalOutlierFactor(n_neighbors=n_neighbors, novelty=True, n_jobs=-1)

    fit_n = min(len(X), 5000)
    np.random.seed(42)
    idx = np.random.choice(len(X), size=fit_n, replace=False) if len(X) > fit_n else np.arange(len(X))
    lof.fit(X[idx])

    # Fast chunked decision function
    chunk_size = 10000
    raw_scores = []
    for start in range(0, len(X), chunk_size):
        chunk_scores = -1.0 * lof.decision_function(X[start:start+chunk_size])
        raw_scores.append(chunk_scores)

    raw_scores = np.concatenate(raw_scores)

    if save_model:
        model_dir = os.path.join("data", "ml_anomaly", "models")
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, f"lof_{model_version}.joblib")
        joblib.dump(lof, model_path)
        print(f"[ML ANOMALY] Saved versioned LOF model to {model_path}")

    return raw_scores, lof
