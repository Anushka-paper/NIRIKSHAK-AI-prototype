import os
import sys
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "backend/app"))

from ingestion.entity_resolution.normalizers import normalize_text
from ingestion.entity_resolution.work_id_parser import parse_work_id
from ingestion.entity_resolution.similarity import SimilarityEngine
from ingestion.entity_resolution.scoring import ContextualScorer
from ingestion.entity_resolution.confidence import ConfidenceClassifier

class TestEntityResolution(unittest.TestCase):

    def test_mp_normalization(self):
        res1 = normalize_text("Shri Narendra Modi", entity_type="mp")
        res2 = normalize_text("NARENDRA MODI", entity_type="mp")
        self.assertEqual(res1["normalized_value"], "narendra modi")
        self.assertEqual(res2["normalized_value"], "narendra modi")

    def test_vendor_normalization(self):
        res1 = normalize_text("M/s ABC Construction Pvt. Ltd.", entity_type="vendor")
        res2 = normalize_text("ABC Construction Private Limited", entity_type="vendor")
        self.assertEqual(res1["normalized_value"], "abc construction private limited")
        self.assertEqual(res2["normalized_value"], "abc construction private limited")

    def test_work_id_parsing(self):
        parsed = parse_work_id("EDU-1-2023-0001 - Classroom Construction")
        self.assertEqual(parsed, "EDU-1-2023-0001")

    def test_similarity_engine(self):
        sim = SimilarityEngine.composite_string_similarity("ravi kishan", "shri ravi kishan ji")
        self.assertGreater(sim, 0.60)

    def test_confidence_classification(self):
        level_high, status_high = ConfidenceClassifier.classify_confidence(0.92)
        level_med, status_med = ConfidenceClassifier.classify_confidence(0.72)
        level_low, status_low = ConfidenceClassifier.classify_confidence(0.45)

        self.assertEqual(status_high, "AUTO_RESOLVED")
        self.assertEqual(status_med, "REVIEW_REQUIRED")
        self.assertEqual(status_low, "UNRESOLVED")

if __name__ == "__main__":
    unittest.main()

