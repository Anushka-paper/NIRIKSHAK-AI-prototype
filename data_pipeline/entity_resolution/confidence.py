def classify_confidence(score):
    if score >= 0.90:
        return "HIGH", "AUTO_RESOLVED"
    elif score >= 0.75:
        return "MEDIUM", "REVIEW_REQUIRED"
    else:
        return "LOW", "UNRESOLVED"
