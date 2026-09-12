"""
Inference entry point for the delay risk model. A single function,
`predict_delay_risk()`, that both live services (backend/backend_api.py
and, if it's ever actually wired up, backend/main.py) can call instead
of duplicating hash-seeded fake logic.

Deliberately does NOT take "days already elapsed since sanction" as a
model input -- the model is trained on sanction-time-only features (see
dataset.py's leakage note), so it answers "how risky is this work given
what was known at sanction" rather than pretending to model elapsed-time
hazard from a single historical snapshot with no intermediate
timestamps. Callers that have a live "already overdue" fact (elapsed
days > statutory SLA) should treat that as a separate, transparent
override on top of this score -- see backend/backend_api.py's use of
this function for exactly that pattern.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import pandas as pd

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "delay_risk_model.joblib"

_bundle_cache: Optional[dict] = None
_explainer_cache = None

FeatureKwargs = Dict[str, Any]


def _load_bundle() -> Optional[dict]:
    global _bundle_cache
    if _bundle_cache is None and MODEL_PATH.exists():
        try:
            _bundle_cache = joblib.load(MODEL_PATH)
        except Exception as e:
            print(f"delay risk model failed to load ({MODEL_PATH}): {e}")
            _bundle_cache = None
    return _bundle_cache


def is_model_available() -> bool:
    return _load_bundle() is not None


def _build_input_row(bundle: dict, **kwargs) -> Dict[str, Any]:
    medians = bundle.get("feature_medians", {})
    row = {
        "sanctioned_amount": kwargs.get("sanctioned_amount"),
        "recommended_amount": kwargs.get("recommended_amount") if kwargs.get("recommended_amount") is not None else kwargs.get("sanctioned_amount"),
        "recommendation_to_sanction_days": kwargs.get("recommendation_to_sanction_days"),
        "mp_historical_completion_rate": kwargs.get("mp_historical_completion_rate"),
        "state_historical_completion_rate": kwargs.get("state_historical_completion_rate"),
        "constituency_historical_completion_rate": kwargs.get("constituency_historical_completion_rate"),
        "vendor_historical_completion_rate": kwargs.get("vendor_historical_completion_rate"),
        "work_description_length": kwargs.get("work_description_length"),
        "work_description_word_count": kwargs.get("work_description_word_count"),
        "amount_percentile": kwargs.get("amount_percentile"),
        "amount_z_score": kwargs.get("amount_z_score"),
        "sanction_month": kwargs.get("sanction_month"),
        "sanction_quarter": kwargs.get("sanction_quarter"),
        "state": kwargs.get("state") or "Unknown",
        "work_category": kwargs.get("work_category") or "Unknown",
    }
    # A live caller (e.g. a quick "estimated_cost + state + category"
    # check from the UI) won't know most of these -- impute with the
    # training-set median rather than leaving NaN, so the prediction
    # reflects "a typical work of this kind" on the unknown dimensions.
    for col in bundle.get("numeric_features", []):
        if row.get(col) is None:
            row[col] = medians.get(col)
    return row


def _encode_row(bundle: dict, row: Dict[str, Any]) -> pd.DataFrame:
    df_in = pd.DataFrame([row])[bundle["feature_names"]]
    for col in bundle["categorical_features"]:
        enc = bundle["encoders"][col]
        df_in[[col]] = enc.transform(df_in[[col]].astype(str))
    return df_in


def predict_delay_risk(
    sanctioned_amount: float,
    recommended_amount: Optional[float] = None,
    recommendation_to_sanction_days: Optional[float] = None,
    state: Optional[str] = None,
    work_category: Optional[str] = None,
    mp_historical_completion_rate: Optional[float] = None,
    state_historical_completion_rate: Optional[float] = None,
    constituency_historical_completion_rate: Optional[float] = None,
    vendor_historical_completion_rate: Optional[float] = None,
    work_description_length: Optional[float] = None,
    work_description_word_count: Optional[float] = None,
    amount_percentile: Optional[float] = None,
    amount_z_score: Optional[float] = None,
    sanction_month: Optional[int] = None,
    sanction_quarter: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Returns None if the trained model artifact isn't available (caller
    should fall back to a clearly-labeled heuristic, never crash or
    silently fabricate a number here).
    """
    bundle = _load_bundle()
    if bundle is None:
        return None

    row = _build_input_row(
        bundle,
        sanctioned_amount=sanctioned_amount, recommended_amount=recommended_amount,
        recommendation_to_sanction_days=recommendation_to_sanction_days, state=state,
        work_category=work_category, mp_historical_completion_rate=mp_historical_completion_rate,
        state_historical_completion_rate=state_historical_completion_rate,
        constituency_historical_completion_rate=constituency_historical_completion_rate,
        vendor_historical_completion_rate=vendor_historical_completion_rate,
        work_description_length=work_description_length,
        work_description_word_count=work_description_word_count,
        amount_percentile=amount_percentile, amount_z_score=amount_z_score,
        sanction_month=sanction_month, sanction_quarter=sanction_quarter,
    )
    df_in = _encode_row(bundle, row)

    clf = bundle["model"]
    probs = clf.predict_proba(df_in)[0]
    classes = bundle["classes"]
    pred_idx = int(probs.argmax())

    return {
        "risk_level": classes[pred_idx],
        "risk_probability": round(float(probs[pred_idx]), 4),
        "delayed_probability": round(float(probs[classes.index("HIGH")]), 4),
        "model_version": bundle.get("model_version"),
        "trained_at": bundle.get("trained_at"),
        "training_rows": bundle.get("training_rows"),
    }


def explain_delay_risk(**feature_kwargs: FeatureKwargs) -> Optional[List[Dict[str, Any]]]:
    """
    Real per-prediction SHAP feature contributions for the same input a
    predict_delay_risk() call would take -- this is the "already-
    computed, already-grounded structured evidence" Epic 6's LLM layer
    is required to reason over rather than inventing. Returns None if
    the model (or SHAP) isn't available; never fabricates a contribution.

    Each entry: {feature, value, shap_value, direction}. direction is
    "increases_risk" / "decreases_risk" relative to the model's own
    base rate, not an arbitrary label.
    """
    global _explainer_cache
    bundle = _load_bundle()
    if bundle is None:
        return None

    try:
        import shap
    except ImportError:
        return None

    row = _build_input_row(bundle, **feature_kwargs)
    df_in = _encode_row(bundle, row)

    if _explainer_cache is None:
        _explainer_cache = shap.TreeExplainer(bundle["model"])

    shap_values = _explainer_cache.shap_values(df_in)[0]  # single row, positive (HIGH) class

    contributions = []
    for i, feature in enumerate(bundle["feature_names"]):
        raw_value = row.get(feature)
        # feature_medians (a pandas .to_dict() result) and caller-supplied
        # values can both be numpy scalars, which json.dumps can't handle
        # -- this payload gets cached as JSON downstream, so normalize here.
        if hasattr(raw_value, "item"):
            raw_value = raw_value.item()
        sv = float(shap_values[i])
        contributions.append({
            "feature": feature,
            "value": raw_value,
            "shap_value": round(sv, 4),
            "direction": "increases_risk" if sv > 0 else "decreases_risk",
        })

    contributions.sort(key=lambda c: abs(c["shap_value"]), reverse=True)
    return contributions
