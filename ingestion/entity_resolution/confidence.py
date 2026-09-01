class ConfidenceClassifier:
    """
    Entity Resolution Confidence Classifier.
    Categorizes match scores into HIGH, MEDIUM, and LOW confidence bands.
    """

    HIGH_THRESHOLD = 0.85     # Auto-resolve
    MEDIUM_THRESHOLD = 0.65   # Review required

    @classmethod
    def classify_confidence(cls, confidence_score: float) -> tuple[str, str]:
        """
        Classifies confidence score into (confidence_level, resolution_status).
        HIGH (>= 0.85) -> AUTO_RESOLVED
        MEDIUM (0.65 - 0.84) -> REVIEW_REQUIRED
        LOW (< 0.65) -> UNRESOLVED (Never silently merged!)
        """
        if confidence_score >= cls.HIGH_THRESHOLD:
            return "HIGH", "AUTO_RESOLVED"
        elif confidence_score >= cls.MEDIUM_THRESHOLD:
            return "MEDIUM", "REVIEW_REQUIRED"
        else:
            return "LOW", "UNRESOLVED"

