# Early-Warning System Configuration & Alert Thresholds (§14)

ALERT_PRIORITY_THRESHOLDS = {
    "CRITICAL": 75.0,
    "HIGH": 50.0,
    "MEDIUM": 25.0
}

ALERT_STATUS_ENUM = [
    "NEW",
    "UNDER_INVESTIGATION",
    "VALIDATED_RISK",
    "DISMISSED",
    "DATA_QUALITY_ISSUE"
]

DEFAULT_EVIDENCE_TEMPLATE = {
    "risk_drivers": [],
    "threshold_breached": "",
    "rule_code": "",
    "recommended_action": "",
    "source_signals": []
}

