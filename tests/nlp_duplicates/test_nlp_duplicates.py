import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from data_pipeline.nlp_duplicates.text_cleaner import expand_abbreviations, clean_work_description
from data_pipeline.nlp_duplicates.vectorizer import compute_similarity_matrix
from data_pipeline.nlp_duplicates.candidate_retriever import find_nlp_duplicate_candidates, compute_calibrated_probability

def test_abbreviation_expansion():
    text = "Construction of CC Road near PWD office in GP area"
    expanded = expand_abbreviations(text)
    assert "cement concrete road" in expanded
    assert "public works department" in expanded
    assert "gram panchayat" in expanded

def test_text_cleaner_boilerplate_stripping():
    raw_desc = "Proposed Construction of BT Road under MPLADS scheme"
    cleaned = clean_work_description(raw_desc)
    assert "black top road" in cleaned
    assert "proposed construction of" not in cleaned

def test_similarity_vectorization():
    texts = [
        "cement concrete road construction",
        "cement concrete road development",
        "drinking water supply borewell"
    ]
    sim_matrix = compute_similarity_matrix(texts)
    assert sim_matrix.shape == (3, 3)
    assert sim_matrix[0, 1] > sim_matrix[0, 2]  # Similar roads should have higher similarity

def test_calibrated_probability_logistic_curve():
    prob_high = compute_calibrated_probability(0.95, 3)
    prob_low = compute_calibrated_probability(0.50, 0)
    assert prob_high > 0.85
    assert prob_low < 0.20

def test_candidate_retrieval_pipeline():
    df_dummy = pd.DataFrame([
        {"canonical_work_id": "W1", "work": "Construction of CC Road in GP area", "canonical_mp_name": "MP_A", "canonical_work_category": "ROADS", "sanctioned_amount_inr": 500000},
        {"canonical_work_id": "W2", "work": "Development of Cement Concrete Road in GP area", "canonical_mp_name": "MP_A", "canonical_work_category": "ROADS", "sanctioned_amount_inr": 500000},
    ])
    candidates = find_nlp_duplicate_candidates(df_dummy, similarity_threshold=0.50)
    assert len(candidates) >= 1
    assert candidates[0]["constituency_match"] is True

