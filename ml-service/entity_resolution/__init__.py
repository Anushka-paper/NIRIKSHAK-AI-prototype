"""
NIRIKSHAK-AI Entity Resolution Package.
Dynamic, reusable multi-field entity resolution for MPLADS works and entities.
"""

from .resolver import EntityResolver, resolve_parliament, resolve_all
from .column_mapper import ColumnMapper
from .candidate_generator import CandidateGenerator
from .exact_matcher import ExactMatcher
from .fuzzy_matcher import FuzzyMatcher
from .similarity import calculate_string_similarity, calculate_amount_similarity, calculate_date_compatibility
from .scoring import ScoringEngine
from .confidence import ConfidenceClassifier
from .provenance import ProvenanceManager
from .review_queue import ReviewQueueManager

__all__ = [
    "EntityResolver",
    "resolve_parliament",
    "resolve_all",
    "ColumnMapper",
    "CandidateGenerator",
    "ExactMatcher",
    "FuzzyMatcher",
    "calculate_string_similarity",
    "calculate_amount_similarity",
    "calculate_date_compatibility",
    "ScoringEngine",
    "ConfidenceClassifier",
    "ProvenanceManager",
    "ReviewQueueManager"
]

