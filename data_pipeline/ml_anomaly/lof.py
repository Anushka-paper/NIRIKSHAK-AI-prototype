import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from data_pipeline.ml_anomaly.config import LOF_NEIGHBORS

def train_local_outlier_factor(X):
    if len(X) == 0:
        return np.array([]), None
        
    n_neighbors = min(LOF_NEIGHBORS, max(2, len(X) - 1))
    print(f"[ML ANOMALY] Training Local Outlier Factor (LOF) model (k={n_neighbors})...")
    
    lof = LocalOutlierFactor(n_neighbors=n_neighbors, novelty=True, n_jobs=-1)
    
    # Subsample if N > 10,000 for high efficiency
    if len(X) > 10000:
        np.random.seed(42)
        idx = np.random.choice(len(X), size=10000, replace=False)
        lof.fit(X[idx])
    else:
        lof.fit(X)
        
    raw_scores = -1.0 * lof.decision_function(X)
    return raw_scores, lof
