"""
Assembles the ONLY facts the LLM in investigation.py is allowed to
reason about. Nothing outside this payload should ever reach the model
-- this is what makes the explanation layer safe despite being an LLM:
it composes language over fixed, already-computed evidence (the
HistGradientBoostingClassifier's score + SHAP attributions from Epic 3),
it never touches the score itself or invents a feature contribution.

Design note on "peer baseline": the spec calls for a peer-comparison
baseline (median, 90th percentile, n_obs) so the LLM can flag a thin
sample. We compute this for real from the training data's per-category
distribution -- not fabricated -- and n_obs is the actual group size,
so a rare work_category with few historical peers is visibly thin
rather than silently treated as equally confident.
"""

from typing import Any, Dict, List, Optional


def build_grounding_payload(
    work_id: str,
    risk_score: float,
    risk_band: str,
    shap_contributions: List[Dict[str, Any]],
    peer_baseline: Dict[str, Any],
    work_facts: Dict[str, Any],
) -> Dict[str, Any]:
    """
    risk_score: model's probability for the predicted class (0-1).
    risk_band: "LOW" | "HIGH" (see ml-service/prediction/delay).
    shap_contributions: output of predict.explain_delay_risk() -- list of
        {feature, value, shap_value, direction}, already sorted by |impact|.
    peer_baseline: {median, p90, n_obs, baseline_version} for the work's
        category -- see risk_baseline.py for how this is computed.
    work_facts: raw, human-legible facts about the work (sanction_amount,
        vendor_name, sanction_date, progress_pct, evidence_on_file, ...).
        Only include fields that are true/known; omit unknowns rather
        than sending null placeholders the model might mistake for zero.
    """
    return {
        "work_id": work_id,
        "risk_score": round(float(risk_score), 4),
        "risk_band": risk_band,
        "shap_contributions": [
            {
                "feature": c["feature"],
                "value": c["value"],
                "shap_value": c["shap_value"],
                "direction": c["direction"],
            }
            for c in shap_contributions
        ],
        "peer_baseline": {
            "median": peer_baseline.get("median"),
            "p90": peer_baseline.get("p90"),
            "n_obs": peer_baseline.get("n_obs"),
            "baseline_version": peer_baseline.get("baseline_version"),
        },
        "work_facts": {k: v for k, v in work_facts.items() if v is not None},
    }
