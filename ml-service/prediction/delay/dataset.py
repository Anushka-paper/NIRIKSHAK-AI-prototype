"""
Training-frame construction for the MPLADS work-delay risk model.

Label design (why it isn't a naive "was sanction_to_completion_days >
SLA"): restricting to completed works alone is heavily survivorship-biased
-- a work that has been running 900 days and still isn't finished simply
doesn't appear in the "completed" cohort at all, so a completed-only label
makes almost every historical row look "LOW risk" (verified: 98.8% LOW on
this dataset with that naive approach, which is a useless classifier).

Instead we treat this as a censored/hazard-style problem:
  - completed AND duration <= SLA           -> on-time   (label 0)
  - completed AND duration >  SLA           -> delayed   (label 1)
  - still open AND (snapshot - sanction) > SLA -> delayed (label 1)
    (a work that has ALREADY blown the SLA without completing is a real
    positive, regardless of whether it eventually finishes)
  - still open AND (snapshot - sanction) <= SLA -> EXCLUDED (censored --
    we genuinely don't know yet whether it will finish on time)

This roughly triples the effective positive-class sample size (5,362 vs
~0 real HIGH-risk examples in the naive approach) and avoids labeling
open-and-still-within-SLA works as anything at all.
"""

from pathlib import Path
from typing import Tuple

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[3]  # repo root

# Matches backend/compliance_engine.py's COMPLETION_SLA_DAYS (18 months) --
# keep both in sync if the statutory guideline changes.
COMPLETION_SLA_DAYS = 18 * 30

# Feature columns available at (or shortly after) sanction time -- i.e.
# nothing derived from completion/expenditure outcomes, so the model
# generalizes to a work whose fate isn't known yet. This is the actual
# leakage boundary: excluding total_execution_days, sanction_to_completion_days,
# completion_amount, lifecycle_status, and any chronology-issue flag that
# depends on knowing what happened after sanction.
NUMERIC_FEATURES = [
    "sanctioned_amount",
    "recommended_amount",
    "recommendation_to_sanction_days",
    "mp_historical_completion_rate",
    "state_historical_completion_rate",
    "constituency_historical_completion_rate",
    "vendor_historical_completion_rate",
    "work_description_length",
    "work_description_word_count",
    "amount_percentile",
    "amount_z_score",
    "sanction_month",
    "sanction_quarter",
]
CATEGORICAL_FEATURES = ["state", "work_category"]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def _load_raw() -> pd.DataFrame:
    dfs = []
    for parliament in ("lok_sabha", "rajya_sabha"):
        path = BASE_DIR / "data" / "features" / parliament / "work_features.csv"
        if path.exists():
            dfs.append(pd.read_csv(path, low_memory=False))
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def build_training_frame(snapshot_date: str = "2026-09-08") -> Tuple[pd.DataFrame, pd.Series]:
    """
    Returns (X, y) ready for training: X has FEATURE_COLUMNS only (no
    leakage columns), y is a 0/1 delayed label. Rows with an unresolved
    (censored) outcome are dropped, not mislabeled.
    """
    df = _load_raw()
    if df.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS), pd.Series(dtype=int)

    df["sanction_date"] = pd.to_datetime(df["sanction_date"], errors="coerce")
    df = df[df["sanction_date"].notna()].copy()

    snapshot = pd.Timestamp(snapshot_date)
    elapsed_if_open = (snapshot - df["sanction_date"]).dt.days
    is_completed = df["has_completion"] == True
    duration = pd.to_numeric(df["sanction_to_completion_days"], errors="coerce")

    label = pd.Series(pd.NA, index=df.index, dtype="Int64")
    label[is_completed & duration.notna() & (duration >= 0) & (duration <= COMPLETION_SLA_DAYS)] = 0
    label[is_completed & duration.notna() & (duration > COMPLETION_SLA_DAYS)] = 1
    label[(~is_completed) & (elapsed_if_open > COMPLETION_SLA_DAYS)] = 1
    # still open, within SLA -> stays <NA>, dropped below (censored)

    df["_label"] = label
    labeled = df[df["_label"].notna()].copy()

    missing_cols = [c for c in FEATURE_COLUMNS if c not in labeled.columns]
    if missing_cols:
        raise ValueError(f"work_features.csv is missing expected columns: {missing_cols}")

    X = labeled[FEATURE_COLUMNS].copy()
    y = labeled["_label"].astype(int)
    return X, y


_baseline_cache: dict = {}


def compute_peer_baseline(work_category: str, baseline_version: str = "v1-sanctioned_amount") -> dict:
    """
    Real peer-comparison stats (not fabricated) for Epic 6's grounding
    payload: how does this work's sanctioned amount compare to other
    works in the same category? A thin n_obs (few historical peers in
    an unusual category) is a real signal the LLM is required to flag
    in confidence_note, not something to paper over.
    """
    global _baseline_cache
    if not _baseline_cache:
        df = _load_raw()
        if not df.empty and "sanctioned_amount" in df.columns and "work_category" in df.columns:
            amounts = pd.to_numeric(df["sanctioned_amount"], errors="coerce")
            grouped = pd.DataFrame({"work_category": df["work_category"], "sanctioned_amount": amounts}).dropna()
            _baseline_cache = {
                cat: {
                    "median": float(g["sanctioned_amount"].median()),
                    "p90": float(g["sanctioned_amount"].quantile(0.9)),
                    "n_obs": int(len(g)),
                }
                for cat, g in grouped.groupby("work_category")
            }

    stats = _baseline_cache.get(work_category, {"median": None, "p90": None, "n_obs": 0})
    return {**stats, "baseline_version": baseline_version}
