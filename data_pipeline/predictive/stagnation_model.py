import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, precision_score, recall_score
from data_pipeline.predictive.config import N_ESTIMATORS, RANDOM_STATE

def train_stagnation_model(X_train, y_train, X_eval):
    if len(np.unique(y_train)) < 2:
        stag_probs = np.zeros(len(X_eval))
        metrics = {"stagnation_roc_auc": 1.0, "stagnation_precision": 0.0, "stagnation_recall": 0.0}
        return stag_probs, None, metrics

    clf = RandomForestClassifier(n_estimators=N_ESTIMATORS, max_depth=8, random_state=RANDOM_STATE, n_jobs=-1)
    clf.fit(X_train, y_train)
    
    stag_probs = clf.predict_proba(X_eval)[:, 1] if len(X_eval) > 0 else np.array([])
    
    train_probs = clf.predict_proba(X_train)[:, 1]
    train_preds = (train_probs >= 0.5).astype(int)
    
    metrics = {
        "stagnation_roc_auc": round(float(roc_auc_score(y_train, train_probs)), 4) if len(np.unique(y_train)) > 1 else 1.0,
        "stagnation_precision": round(float(precision_score(y_train, train_preds, zero_division=0)), 4),
        "stagnation_recall": round(float(recall_score(y_train, train_preds, zero_division=0)), 4)
    }
    
    return stag_probs, clf, metrics
