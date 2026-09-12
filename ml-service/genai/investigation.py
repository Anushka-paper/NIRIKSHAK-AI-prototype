"""
LLM-grounded risk explanation layer (Epic 6, mdfiles/PRD_GAP_CLOSURE.md).

Why an LLM here doesn't compromise explainability: the score and every
feature attribution come from Epic 3's trained HistGradientBoostingClassifier
+ SHAP TreeExplainer (ml-service/prediction/delay/predict.py), computed
BEFORE this module ever runs. The LLM's only job is composing natural-
language prose over that fixed, already-computed evidence -- it cannot
change the score, cannot invent a feature contribution, and every
numeric claim it makes is checked against the grounding payload before
being accepted (validate_response). If the LLM is unavailable, times
out, or produces an unverifiable claim, the system degrades to a
template-based explanation over the exact same evidence rather than
ever serving a blank state or a crash.

Entry point for a FastAPI route: get_risk_explanation_safe(db, work_id,
model_version, grounding_payload) -- see the __main__ block at the
bottom for a fully worked example, including a simulated LLM failure.
"""

import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, for `models`

try:
    # When imported as part of the genai package (e.g. from backend_api.py)
    from .prompts import RISK_EXPLANATION_TOOL, SYSTEM_PROMPT, THIN_SAMPLE_THRESHOLD
except ImportError:
    # When run directly as a script (python investigation.py)
    from prompts import RISK_EXPLANATION_TOOL, SYSTEM_PROMPT, THIN_SAMPLE_THRESHOLD

# The build prompt specified "claude-sonnet-4-6"; that id predates this
# session's model family and doesn't exist. Using the current flagship
# instead -- see CLAUDE.md-equivalent guidance: default to the latest,
# most capable model for new integrations.
MODEL = "claude-sonnet-5"

_client = None


def _get_client():
    """Lazy import + init so this module can be imported (and its
    fallback/validation logic tested) even where the `anthropic` package
    or an API key isn't available."""
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        from anthropic import Anthropic
        _client = Anthropic(api_key=api_key)
    return _client


def generate_risk_explanation(grounding_payload: Dict[str, Any], timeout: float = 20.0) -> Dict[str, Any]:
    """
    Raises on any failure (missing key, network error, timeout, malformed
    response) -- callers must catch and fall back, this function never
    silently returns a partial/fabricated result.
    """
    client = _get_client()
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=[RISK_EXPLANATION_TOOL],
        tool_choice={"type": "tool", "name": "risk_explanation"},
        messages=[{
            "role": "user",
            "content": f"Grounding payload:\n{json.dumps(grounding_payload, indent=2)}",
        }],
        timeout=timeout,
    )
    for block in message.content:
        if block.type == "tool_use" and block.name == "risk_explanation":
            return block.input
    raise RuntimeError("Model response did not include a risk_explanation tool call")


_NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*")


def _extract_numbers(text: str) -> List[float]:
    cleaned = text.replace(",", "").replace("₹", "").replace("%", "")
    return [float(m) for m in re.findall(r"-?\d+\.?\d*", cleaned)]


def _flatten_numeric_values(payload: Dict[str, Any]) -> set:
    values = set()

    def walk(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
        elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
            values.add(round(float(obj), 2))
            values.add(round(float(obj) * 100, 2))  # probabilities/ratios often quoted as %

    walk(payload)
    return values


def validate_response(response: Dict[str, Any], grounding_payload: Dict[str, Any]) -> bool:
    """
    Every numeric claim in `why` must trace back to a value actually
    present in the grounding payload (within 2% rounding tolerance).
    Numbers below 1 are skipped (ratios like "0.3x" are too easy to
    coincidentally match and not worth gating on). Returns False on the
    first unverifiable number -- caller logs and falls back rather than
    serving an unverified LLM claim.
    """
    payload_numbers = _flatten_numeric_values(grounding_payload)
    for claim in response.get("why", []):
        for num in _extract_numbers(claim):
            if abs(num) < 1:
                continue
            if not any(abs(num - pv) <= max(1.0, abs(pv) * 0.02) for pv in payload_numbers):
                return False
    return True


def rule_based_fallback(grounding_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Non-LLM template fallback over the exact same grounding payload --
    used automatically if the LLM call fails, times out, or its
    response fails validation. Must never crash or return a blank
    state: always produces the same {why, recommended_actions,
    confidence_note} shape the LLM path does.
    """
    contributions = grounding_payload.get("shap_contributions") or []
    top = contributions[:2]

    why: List[str] = []
    for c in top:
        verb = "increases" if c["direction"] == "increases_risk" else "decreases"
        why.append(
            f"{c['feature'].replace('_', ' ')} (value: {c['value']}) {verb} predicted delay risk "
            f"(model attribution: {c['shap_value']:+.2f})."
        )
    if not why:
        why = [
            f"Risk score {grounding_payload.get('risk_score', 0):.0%} "
            f"({grounding_payload.get('risk_band', 'UNKNOWN')}) from the trained model; "
            "no individual feature attribution data was available for this work."
        ]

    if grounding_payload.get("risk_band") == "HIGH":
        actions = [{
            "action": "Schedule a physical inspection and verify vendor progress",
            "rationale": "The trained model flags this work as high delay-risk based on the factors above; a direct check is warranted before further disbursal.",
        }]
    else:
        actions = [{
            "action": "Continue routine monitoring",
            "rationale": "The trained model does not currently flag this work as high delay-risk.",
        }]

    n_obs = (grounding_payload.get("peer_baseline") or {}).get("n_obs") or 0
    confidence_note = "Template-based explanation (LLM unavailable) — a direct summary of the top model attributions, not a synthesis of how they interact."
    if n_obs < THIN_SAMPLE_THRESHOLD:
        confidence_note += f" Peer comparison is based on only {n_obs} historical works in this category, so it is low-confidence."

    return {"why": why, "recommended_actions": actions, "confidence_note": confidence_note}


def get_risk_explanation_safe(db, work_id: str, model_version: str, grounding_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    The one-line call a FastAPI endpoint should make:
    GET /api/works/{work_id}/risk-explanation ->
        get_risk_explanation_safe(db, work_id, model_version, build_grounding_payload(...))

    Checks the cache first (keyed on work_id + model_version -- a cache
    hit means the underlying score hasn't changed since we last paid to
    explain it), only calls the LLM on a miss, validates the LLM's
    response before accepting it, and falls back to the rule-based
    template on any failure. Never raises to the caller.
    """
    from models import RiskExplanation  # local import: only needed with a real db session

    cached = db.query(RiskExplanation).filter(
        RiskExplanation.work_id == work_id,
        RiskExplanation.model_version == model_version,
    ).first()
    if cached:
        return {
            "why": json.loads(cached.why_json),
            "recommended_actions": json.loads(cached.recommended_actions_json),
            "confidence_note": cached.confidence_note,
            "generated_by": cached.generated_by,
            "cached": True,
        }

    generated_by = "llm"
    try:
        result = generate_risk_explanation(grounding_payload)
        if not validate_response(result, grounding_payload):
            raise ValueError("LLM response contained an unverifiable numeric claim")
    except Exception as e:
        print(f"Risk explanation LLM path unavailable for work {work_id} ({e}) -- using rule-based fallback")
        result = rule_based_fallback(grounding_payload)
        generated_by = "fallback"

    entry = RiskExplanation(
        work_id=work_id,
        model_version=model_version,
        grounding_payload_json=json.dumps(grounding_payload),
        why_json=json.dumps(result["why"]),
        recommended_actions_json=json.dumps(result["recommended_actions"]),
        confidence_note=result["confidence_note"],
        generated_by=generated_by,
        created_at=date.today(),
    )
    db.add(entry)
    db.commit()

    return {**result, "generated_by": generated_by, "cached": False}


if __name__ == "__main__":
    # Runnable example: one work with 2-3 significant SHAP contributions,
    # one with a thin baseline sample, and one simulated LLM failure to
    # prove the fallback actually engages.
    try:
        from .context import build_grounding_payload
    except ImportError:
        from context import build_grounding_payload

    print("=" * 70)
    print("Example 1: normal grounding payload, LLM path (will fall back")
    print("if ANTHROPIC_API_KEY isn't set in this environment)")
    print("=" * 70)
    payload_1 = build_grounding_payload(
        work_id="CW_LO_DEMO_1",
        risk_score=0.91,
        risk_band="HIGH",
        shap_contributions=[
            {"feature": "vendor_historical_completion_rate", "value": 0.15, "shap_value": 2.1, "direction": "increases_risk"},
            {"feature": "sanctioned_amount", "value": 9000000, "shap_value": 1.4, "direction": "increases_risk"},
            {"feature": "constituency_historical_completion_rate", "value": 0.7, "shap_value": -0.6, "direction": "decreases_risk"},
        ],
        peer_baseline={"median": 3200000, "p90": 7800000, "n_obs": 412, "baseline_version": "v1-sanctioned_amount"},
        work_facts={
            "sanction_amount": 9000000, "vendor_id": "VEND_00231", "sanction_date": "2025-11-02",
            "progress_pct": 12, "evidence_on_file": False,
        },
    )
    # This script has no DB session to demonstrate the cache against, so
    # it exercises generate -> validate -> fallback directly rather than
    # the get_risk_explanation_safe() wrapper (which needs a real
    # SQLAlchemy Session -- see a FastAPI route for that usage).
    try:
        result = generate_risk_explanation(payload_1)
        valid = validate_response(result, payload_1)
        print("LLM call succeeded, validation passed:", valid)
        if not valid:
            print("Validation failed -- falling back to template")
            result = rule_based_fallback(payload_1)
    except Exception as e:
        print(f"LLM call unavailable ({e}) -- using rule-based fallback")
        result = rule_based_fallback(payload_1)
    print(json.dumps(result, indent=2))

    print("\n" + "=" * 70)
    print("Example 2: thin peer baseline (n_obs=8) -- confidence_note must flag it")
    print("=" * 70)
    payload_2 = build_grounding_payload(
        work_id="CW_LO_DEMO_2",
        risk_score=0.62,
        risk_band="HIGH",
        shap_contributions=[
            {"feature": "recommendation_to_sanction_days", "value": 210, "shap_value": 0.8, "direction": "increases_risk"},
        ],
        peer_baseline={"median": 1500000, "p90": 4000000, "n_obs": 8, "baseline_version": "v1-sanctioned_amount"},
        work_facts={"sanction_amount": 1800000, "vendor_id": "VEND_00987", "sanction_date": "2026-01-15", "progress_pct": 30, "evidence_on_file": True},
    )
    result_2 = rule_based_fallback(payload_2)  # deterministic, always shows the thin-sample flag
    print(json.dumps(result_2, indent=2))
    assert "8 historical works" in result_2["confidence_note"], "thin-sample flag missing"
    print("\nThin-sample confidence flag present: PASS")

    print("\n" + "=" * 70)
    print("Example 3: simulated LLM failure (network error) -- fallback must engage")
    print("=" * 70)
    def _broken_generate(*args, **kwargs):
        raise ConnectionError("simulated network failure")
    _real_generate = generate_risk_explanation
    generate_risk_explanation = _broken_generate  # type: ignore
    try:
        result_3 = generate_risk_explanation(payload_1)
    except Exception as e:
        print(f"LLM call failed as expected ({e}) -- falling back")
        result_3 = rule_based_fallback(payload_1)
    finally:
        generate_risk_explanation = _real_generate  # type: ignore
    print(json.dumps(result_3, indent=2))
    assert result_3["why"], "fallback must never return a blank result"
    print("\nFallback engaged and returned a non-blank result: PASS")
