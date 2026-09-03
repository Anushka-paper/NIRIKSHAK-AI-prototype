"""
Comprehensive Unit and Integration Tests for Dynamic Entity Resolution Engine.
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "ml-service"))

from entity_resolution.column_mapper import ColumnMapper
from entity_resolution.normalizer import (
    normalize_text,
    normalize_mp_name,
    normalize_constituency,
    normalize_work_id,
    normalize_amount_to_float
)
from entity_resolution.similarity import (
    calculate_string_similarity,
    calculate_amount_similarity,
    calculate_date_compatibility
)
from entity_resolution.candidate_generator import CandidateGenerator
from entity_resolution.exact_matcher import ExactMatcher
from entity_resolution.fuzzy_matcher import FuzzyMatcher
from entity_resolution.scoring import ScoringEngine
from entity_resolution.confidence import ConfidenceClassifier
from entity_resolution.provenance import ProvenanceManager
from entity_resolution.resolver import EntityResolver

def test_semantic_column_detection():
    mapper = ColumnMapper()
    df = pd.DataFrame({
        "Hon'ble Members of Parliament": ["Ram"],
        "State": ["UP"],
        "Constituency": ["Lucknow"],
        "Sanctioned Amount": [500000],
        "Work ID": ["W123"],
        "Work Description": ["Road work"]
    })
    mapping = mapper.detect_semantic_columns(df)
    assert mapping["mp_name"] == "Hon'ble Members of Parliament"
    assert mapping["state"] == "State"
    assert mapping["constituency"] == "Constituency"
    assert mapping["amount"] == "Sanctioned Amount"
    assert mapping["work_id"] == "Work ID"
    assert mapping["work_description"] == "Work Description"

def test_normalization_utilities():
    assert normalize_mp_name("Hon'ble Shri Ram Singh") == "ram singh"
    assert normalize_mp_name("Smt. Sita Devi") == "sita devi"
    assert normalize_constituency("FARIDKOT(SC)") == "faridkot"
    assert normalize_constituency("Lucknow (U.P.)") == "lucknow"
    assert normalize_work_id("  WS/123/456  ") == "WS/123/456"
    assert normalize_amount_to_float("₹ 1,50,000.00") == 150000.0

def test_string_and_amount_similarity():
    # Fuzzy description matching
    desc1 = "Construction of road in village A"
    desc2 = "Construction of village road at A"
    sim = calculate_string_similarity(desc1, desc2)
    assert sim >= 70.0

    # Amount similarity within tolerance
    amt_sim = calculate_amount_similarity(100000.0, 105000.0) # 5% difference
    assert amt_sim >= 80.0

    # Major amount difference penalty
    amt_diff_sim = calculate_amount_similarity(100000.0, 500000.0)
    assert amt_diff_sim < 40.0

def test_exact_work_id_matching():
    matcher = ExactMatcher()
    row_a = pd.Series({"work_id": "WS/2024/9999", "work_desc": "Hall"})
    row_b = pd.Series({"project_id": "WS/2024/9999", "desc": "Hall Construction"})
    map_a = {"work_id": "work_id", "work_description": "work_desc"}
    map_b = {"work_id": "project_id", "work_description": "desc"}

    res = matcher.match(row_a, row_b, map_a, map_b)
    assert res is not None
    assert res["is_match"] is True
    assert res["match_method"] == "exact_work_id"
    assert res["confidence_level"] == "HIGH"

def test_multi_field_fuzzy_matching_and_scoring():
    fuzzy = FuzzyMatcher()
    scoring = ScoringEngine()
    classifier = ConfidenceClassifier()

    row_a = pd.Series({
        "mp": "Shri Narendra Modi",
        "state": "Uttar Pradesh",
        "constituency": "Varanasi",
        "description": "Installation of Solar Street Lights at Ward 10",
        "amount": 250000.0
    })
    row_b = pd.Series({
        "mp_name": "Narendra Modi",
        "state": "Uttar Pradesh",
        "constituency": "Varanasi",
        "work_description": "Solar Street Lights Installation at Ward 10",
        "amount": 248000.0
    })
    map_a = {"mp_name": "mp", "state": "state", "constituency": "constituency", 
             "work_description": "description", "amount": "amount"}
    map_b = {"mp_name": "mp_name", "state": "state", "constituency": "constituency", 
             "work_description": "work_description", "amount": "amount"}

    field_scores = fuzzy.evaluate_pair(row_a, row_b, map_a, map_b)
    composite_score, _ = scoring.compute_composite_score(field_scores)
    conf_level, decision = classifier.classify(composite_score)

    assert composite_score >= 85.0
    assert conf_level == "HIGH"
    assert decision == "MATCH"

def test_unrelated_records_rejected():
    fuzzy = FuzzyMatcher()
    scoring = ScoringEngine()
    classifier = ConfidenceClassifier()

    row_a = pd.Series({
        "mp": "Ram Singh",
        "state": "Bihar",
        "constituency": "Patna",
        "description": "Construction of primary health center",
        "amount": 5000000.0
    })
    row_b = pd.Series({
        "mp_name": "Suresh Kumar",
        "state": "Kerala",
        "constituency": "Wayanad",
        "work_description": "Drinking water pipeline repair",
        "amount": 50000.0
    })
    map_a = {"mp_name": "mp", "state": "state", "constituency": "constituency", 
             "work_description": "description", "amount": "amount"}
    map_b = {"mp_name": "mp_name", "state": "state", "constituency": "constituency", 
             "work_description": "work_description", "amount": "amount"}

    field_scores = fuzzy.evaluate_pair(row_a, row_b, map_a, map_b)
    composite_score, _ = scoring.compute_composite_score(field_scores)
    conf_level, decision = classifier.classify(composite_score)

    assert composite_score < 40.0
    assert conf_level == "LOW"
    assert decision == "NO_MATCH"

def test_provenance_and_idempotency():
    prov = ProvenanceManager()
    id1 = prov.get_or_create_canonical_id("WS/100", "recommended", 1)
    prov.link_entities(id1, "WS/100", "sanctioned", 10)

    # Calling again for same record gives identical ID
    id2 = prov.get_or_create_canonical_id("WS/100", "sanctioned", 10)
    assert id1 == id2
    assert id1.startswith("CW_")

def test_end_to_end_entity_resolution_execution(tmp_path):
    # Create two minimal mock standardized datasets
    out_dir = tmp_path / "entity_resolution"
    std_dir = tmp_path / "standardized"
    std_dir.mkdir(parents=True, exist_ok=True)

    df_rec = pd.DataFrame({
        "sr_no": [1, 2],
        "state": ["Karnataka", "Bihar"],
        "constituency": ["DHARWAD", "PATNA"],
        "mp_name": ["Pralhad Venkatesh Joshi", "Ravi Shankar Prasad"],
        "work_description": ["Construction of Community Bhavan at Navalgund", "School room construction"],
        "recommended_amount": [500000.0, 300000.0]
    })
    df_rec.to_csv(std_dir / "recommended_standardized.csv", index=False)

    df_sanc = pd.DataFrame({
        "sr_no": [1, 2],
        "state": ["Karnataka", "Bihar"],
        "constituency": ["DHARWAD", "PATNA"],
        "mp_name": ["Hon'ble Shri Pralhad Venkatesh Joshi", "Ravi Shankar Prasad"],
        "work_description": ["Construction of Community Bhavan Navalgund", "School room construction"],
        "sanction_amount": [497000.0, 300000.0],
        "work_id": ["W_1001", "W_1002"]
    })
    df_sanc.to_csv(std_dir / "sanctioned_standardized.csv", index=False)

    resolver = EntityResolver(
        parliament="lok_sabha",
        standardized_dir=std_dir,
        output_dir=out_dir
    )
    summary = resolver.run()

    assert summary["datasets_discovered"] == 2
    assert summary["total_high_confidence_matches"] >= 2
    assert (out_dir / "entity_resolution_matches.csv").exists()
    assert (out_dir / "review_queue.csv").exists()
    assert (out_dir / "entity_resolution_report.json").exists()

