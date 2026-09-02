import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, precision_score, recall_score
from data_pipeline.predictive.config import N_ESTIMATORS, RANDOM_STATE

def train_cost_model(X_train, y_train, X_eval):
    if len(np.unique(y_train)) < 2:
        cost_probs = np.zeros(len(X_eval))
        metrics = {"cost_roc_auc": 1.0, "cost_precision": 0.0, "cost_recall": 0.0}
        return cost_probs, None, metrics

    clf = GradientBoostingClassifier(n_estimators=N_ESTIMATORS, max_depth=5, random_state=RANDOM_STATE)
    clf.fit(X_train, y_train)
    
    cost_probs = clf.predict_proba(X_eval)[:, 1] if len(X_eval) > 0 else np.array([])
    
    train_probs = clf.predict_proba(X_train)[:, 1]
    train_preds = (train_probs >= 0.5).astype(int)
    
    metrics = {
        "cost_roc_auc": round(float(roc_auc_score(y_train, train_probs)), 4) if len(np.unique(y_train)) > 1 else 1.0,
        "cost_precision": round(float(precision_score(y_train, train_preds, zero_division=0)), 4),
        "cost_recall": round(float(recall_score(y_train, train_preds, zero_division=0)), 4)
    }
    
    return cost_probs, clf, metrics
