import os
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from data_pipeline.ml_anomaly.config import ISO_ESTIMATORS, ISO_CONTAMINATION, RANDOM_STATE

def train_isolation_forest(X, save_model=True):
    if len(X) == 0:
        return np.array([]), None
        
    print(f"[ML ANOMALY] Training Isolation Forest model on {len(X):,} feature vectors...")
    clf = IsolationForest(n_estimators=ISO_ESTIMATORS, contamination=ISO_CONTAMINATION, random_state=RANDOM_STATE, n_jobs=-1)
    clf.fit(X)
    
    # Higher score = more anomalous
    raw_scores = -1.0 * clf.decision_function(X)
    
    if save_model:
        model_dir = os.path.join("data", "ml_anomaly")
        os.makedirs(model_dir, exist_ok=True)
        joblib.dump(clf, os.path.join(model_dir, "isolation_forest.joblib"))
        
    return raw_scores, clf
