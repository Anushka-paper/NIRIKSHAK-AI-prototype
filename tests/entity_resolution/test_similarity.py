import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
from data_pipeline.entity_resolution.similarity import compute_string_similarity

def test_similarity_scoring():
    assert compute_string_similarity("Ravi Kishan", "Ravi Kishan") == 1.0
    assert compute_string_similarity("ABC Construction", "ABC Constructions") > 0.8
