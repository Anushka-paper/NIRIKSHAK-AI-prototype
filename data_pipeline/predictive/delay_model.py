import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import roc_auc_score, mean_absolute_error, precision_score, recall_score
from data_pipeline.predictive.config import N_ESTIMATORS, RANDOM_STATE

def train_delay_models(X_train, y_clf_train, y_reg_train, X_eval):
    if len(np.unique(y_clf_train)) < 2:
        delay_probs = np.zeros(len(X_eval))
        clf = None
        metrics = {"delay_roc_auc": 1.0, "delay_precision": 0.0, "delay_recall": 0.0, "delay_mae_days": 0.0}
    else:
        clf = RandomForestClassifier(n_estimators=N_ESTIMATORS, max_depth=10, random_state=RANDOM_STATE, n_jobs=-1)
        clf.fit(X_train, y_clf_train)
        delay_probs = clf.predict_proba(X_eval)[:, 1] if len(X_eval) > 0 else np.array([])
        
        train_probs = clf.predict_proba(X_train)[:, 1]
        train_preds = (train_probs >= 0.5).astype(int)
        
        metrics = {
            "delay_roc_auc": round(float(roc_auc_score(y_clf_train, train_probs)), 4),
            "delay_precision": round(float(precision_score(y_clf_train, train_preds, zero_division=0)), 4),
            "delay_recall": round(float(recall_score(y_clf_train, train_preds, zero_division=0)), 4),
        }

    reg = RandomForestRegressor(n_estimators=N_ESTIMATORS, max_depth=10, random_state=RANDOM_STATE, n_jobs=-1)
    reg.fit(X_train, y_reg_train)
    delay_days_pred = np.maximum(0.0, reg.predict(X_eval)) if len(X_eval) > 0 else np.array([])
    metrics["delay_mae_days"] = round(float(mean_absolute_error(y_reg_train, reg.predict(X_train))), 2)

    return delay_probs, delay_days_pred, clf, reg, metrics
