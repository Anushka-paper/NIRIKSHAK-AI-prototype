"""
Held-out evaluation for the delay risk classifier. Reports precision/
recall/F1 per class (not just accuracy) since the label is imbalanced
(~78% on-time / 22% delayed) -- accuracy alone would look good for a
classifier that just always predicts "on-time".
"""

from typing import Any, Dict

import numpy as np
from sklearn.metrics import (
    precision_recall_fscore_support,
    roc_auc_score,
    confusion_matrix,
    accuracy_score,
)


def evaluate_model(clf, X_test, y_test) -> Dict[str, Any]:
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]  # P(delayed)

    precision, recall, f1, support = precision_recall_fscore_support(
        y_test, y_pred, labels=[0, 1], zero_division=0
    )
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()

    return {
        "n_test": int(len(y_test)),
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
        "on_time": {
            "precision": round(float(precision[0]), 4),
            "recall": round(float(recall[0]), 4),
            "f1": round(float(f1[0]), 4),
            "support": int(support[0]),
        },
        "delayed": {
            "precision": round(float(precision[1]), 4),
            "recall": round(float(recall[1]), 4),
            "f1": round(float(f1[1]), 4),
            "support": int(support[1]),
        },
        "confusion_matrix": {
            "true_negative": int(tn), "false_positive": int(fp),
            "false_negative": int(fn), "true_positive": int(tp),
        },
    }
