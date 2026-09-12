"""
Trains the real MPLADS work-delay risk classifier, replacing the
hash-seeded pseudo-random logic previously living in
backend/backend_api.py's /api/v1/predict and backend/main.py's dormant
(and, on inspection, already-broken/version-incompatible) equivalent.

Run directly: `python -m ml_service.prediction.delay.train` from the
repo root, or `python train.py` from this directory.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import build_training_frame, FEATURE_COLUMNS, NUMERIC_FEATURES, CATEGORICAL_FEATURES
from evaluate import evaluate_model

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "delay_risk_model.joblib"
METRICS_PATH = Path(__file__).resolve().parents[2] / "models" / "delay_risk_model_metrics.json"


def train(random_state: int = 42, test_size: float = 0.2) -> dict:
    X, y = build_training_frame()
    if X.empty:
        raise RuntimeError("No training data available -- work_features.csv not found under data/features/")

    print(f"Loaded {len(X)} labeled rows (positive/delayed rate: {y.mean():.1%})")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    encoders = {}
    X_train_enc = X_train.copy()
    X_test_enc = X_test.copy()
    for col in CATEGORICAL_FEATURES:
        enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        X_train_enc[[col]] = enc.fit_transform(X_train[[col]].astype(str))
        X_test_enc[[col]] = enc.transform(X_test[[col]].astype(str))
        encoders[col] = enc

    # HistGradientBoostingClassifier: handles NaN natively (this dataset
    # has real missing values in historical-rate columns for
    # first-time MPs/vendors), no scaling needed, and matches the
    # algorithm backend/main.py's dormant integration already claimed to
    # use -- so that existing (previously non-functional) code path
    # becomes true, not just this one.
    clf = HistGradientBoostingClassifier(random_state=random_state, max_iter=200)
    clf.fit(X_train_enc, y_train)

    metrics = evaluate_model(clf, X_test_enc, y_test)
    print(json.dumps(metrics, indent=2))

    bundle = {
        "model": clf,
        "feature_names": FEATURE_COLUMNS,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "encoders": encoders,
        "classes": ["LOW", "HIGH"],  # index-aligned with sorted clf.classes_ == [0, 1]
        # Live callers (e.g. a District Authority pre-checking a brand-new
        # work) usually only know a handful of fields -- amount, state,
        # category. Storing training-set medians lets predict.py impute
        # the rest instead of requiring the full 118-feature context or
        # leaving them NaN.
        "feature_medians": X[NUMERIC_FEATURES].median(numeric_only=True).to_dict(),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "model_version": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
        "training_rows": len(X),
        "metrics": metrics,
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    print(f"Saved model bundle to {MODEL_PATH}")
    return metrics


if __name__ == "__main__":
    train()
