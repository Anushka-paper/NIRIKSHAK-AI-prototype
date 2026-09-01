import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
from data_pipeline.entity_resolution.confidence import classify_confidence

def test_confidence_classification():
    assert classify_confidence(0.95) == ("HIGH", "AUTO_RESOLVED")
    assert classify_confidence(0.80) == ("MEDIUM", "REVIEW_REQUIRED")
    assert classify_confidence(0.50) == ("LOW", "UNRESOLVED")
