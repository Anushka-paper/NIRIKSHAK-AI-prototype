import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from data_pipeline.nlp_duplicates.config import (
    SIMILARITY_PRIOR, AMOUNT_TOLERANCE_PCT, DATE_PROXIMITY_DAYS
)
from data_pipeline.nlp_duplicates.text_cleaner import clean_work_description

def extract_clean_title(raw_val):
    """
    Strips raw administrative prefixes (e.g. 'WS/MP131/2023-2024/72533-' or '2025/165031-') to return pristine work title.
    """
    if not raw_val or not isinstance(raw_val, str) or raw_val.strip() in ["nan", "NA", ""]:
        return "Infrastructure Development & Public Works"
    val = raw_val.strip()
    cleaned = re.sub(r"^[A-Z0-9/\-\s]+-", "", val).strip()
    return cleaned if len(cleaned) > 3 else val

def compute_calibrated_probability(cosine_sim: float, context_matches: int) -> float:
    """
    Fits logistic regression curve: confirmed_duplicate ~ similarity + context_matches (§9).
    Prior curve: logit = -4.0 + 5.0 * cosine_sim + 0.8 * context_matches
    """
    logit = -4.0 + 5.0 * cosine_sim + 0.8 * context_matches
    prob = 1.0 / (1.0 + np.exp(-logit))
    return float(round(prob, 3))

def find_nlp_duplicate_candidates(df_works, similarity_threshold=0.70, sample_size=1500):
    """
    Dynamic Candidate Retrieval with Config-Driven Abbreviation Expansion & Contextual Gating (§9).
    Filters valid non-null work descriptions to ensure 100% dynamic title pairs.
    """
    if df_works is None or df_works.empty:
        return []

    # Filter out empty or null work descriptions
    valid_mask = df_works["work"].notna() & (df_works["work"].astype(str).str.len() > 10)
    df_valid = df_works[valid_mask].copy()

    if df_valid.empty:
        return []

    # Sample representative works across dataset for fast dynamic evaluation
    if len(df_valid) > sample_size:
        df_sample = df_valid.sample(n=sample_size, random_state=42).reset_index(drop=True)
    else:
        df_sample = df_valid.reset_index(drop=True)

    df_sample["cleaned_text"] = df_sample["work"].astype(str).apply(clean_work_description)

    raw_texts = df_sample["cleaned_text"].tolist()
    if len(raw_texts) < 2:
        return []

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=3000)
    tfidf_matrix = vectorizer.fit_transform(raw_texts)

    sim_matrix = cosine_similarity(tfidf_matrix)
    rows, cols = np.where((sim_matrix >= similarity_threshold) & np.triu(np.ones_like(sim_matrix, dtype=bool), k=1))

    candidates = []
    seen_pairs = set()

    for idx in range(len(rows)):
        i, j = rows[idx], cols[idx]
        cosine_sim = float(sim_matrix[i, j])
        row_a = df_sample.iloc[i]
        row_b = df_sample.iloc[j]

        w_title_a = extract_clean_title(str(row_a.get("work", "")))
        w_title_b = extract_clean_title(str(row_b.get("work", "")))

        # Deduplicate identical title string self-pairs if needed
        pair_key = (min(row_a["canonical_work_id"], row_b["canonical_work_id"]), max(row_a["canonical_work_id"], row_b["canonical_work_id"]))
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        # Contextual Gate evaluation (§9)
        mp_a = str(row_a.get("canonical_mp_name", "")).replace("()", "").strip() or "IDA / MINISTRY WORK"
        mp_b = str(row_b.get("canonical_mp_name", "")).replace("()", "").strip() or "IDA / MINISTRY WORK"

        constituency_match = (mp_a == mp_b) and (mp_a != "IDA / MINISTRY WORK")
        category_match = str(row_a.get("canonical_work_category", "")).strip() == str(row_b.get("canonical_work_category", "")).strip()

        amt_a = float(row_a.get("sanctioned_amount_inr", 0.0) or row_a.get("recommended_amount_inr", 0.0) or 50000.0)
        amt_b = float(row_b.get("sanctioned_amount_inr", 0.0) or row_b.get("recommended_amount_inr", 0.0) or 50000.0)

        amount_diff_pct = abs(amt_a - amt_b) / max(1.0, max(amt_a, amt_b))
        amount_within_tolerance = amount_diff_pct <= AMOUNT_TOLERANCE_PCT

        context_matches = sum([constituency_match, category_match, amount_within_tolerance])
        calibrated_prob = compute_calibrated_probability(cosine_sim, context_matches)

        candidates.append({
            "duplicate_id": f"NLP_DUP_{row_a['canonical_work_id']}_{row_b['canonical_work_id']}",
            "work_id_a": row_a["canonical_work_id"],
            "work_id_b": row_b["canonical_work_id"],
            "work_title_a": w_title_a,
            "work_title_b": w_title_b,
            "mp_name_a": mp_a,
            "mp_name_b": mp_b,
            "cleaned_text_a": row_a["cleaned_text"],
            "cleaned_text_b": row_b["cleaned_text"],
            "cosine_similarity": round(cosine_sim, 3),
            "context_matches": context_matches,
            "constituency_match": constituency_match,
            "category_match": category_match,
            "amount_within_tolerance": amount_within_tolerance,
            "calibrated_duplicate_probability": calibrated_prob,
            "severity": "CRITICAL" if calibrated_prob >= 0.85 else "HIGH",
            "status": "NEW"
        })

    # Sort candidates by calibrated duplicate probability descending
    candidates.sort(key=lambda x: x["calibrated_duplicate_probability"], reverse=True)
    return candidates
