COMPLIANCE_RULES = {
    "R001": {
        "name": "EXP_BEFORE_SANCTION",
        "severity": "CRITICAL",
        "weight": 40,
        "description": "Expenditure date precedes formal sanction date",
        "action": "Immediate compliance audit — payment made prior to sanction"
    },
    "R002": {
        "name": "EXP_EXCEEDS_SANCTION",
        "severity": "HIGH",
        "weight": 25,
        "description": "Cumulative expenditure exceeds sanctioned budget amount",
        "action": "Check for valid revised sanction before escalating"
    },
    "R003": {
        "name": "MISSING_SANCTION_BEFORE_EXP",
        "severity": "CRITICAL",
        "weight": 40,
        "description": "Expenditure disbursed on unsanctioned work",
        "action": "Audit unsanctioned work receiving disbursements"
    },
    "R004": {
        "name": "SANCTION_BEFORE_REC",
        "severity": "HIGH",
        "weight": 25,
        "description": "Sanction date precedes recommendation date",
        "action": "Data sequence verification — sanction precedes recommendation"
    },
    "R005": {
        "name": "COMPLETION_BEFORE_SANCTION",
        "severity": "HIGH",
        "weight": 25,
        "description": "Completion date precedes sanction date",
        "action": "Physical verification — work marked completed prior to sanction"
    },
    "R006": {
        "name": "INVALID_NEGATIVE_AMOUNT",
        "severity": "HIGH",
        "weight": 25,
        "description": "Negative financial amount recorded",
        "action": "Financial data integrity audit"
    },
    "R007": {
        "name": "EXACT_DUPLICATE_PAYMENT",
        "severity": "HIGH",
        "weight": 25,
        "description": "Identical transaction amount, vendor, date, and work ID",
        "action": "Payment transaction de-duplication review"
    },
    "R008": {
        "name": "MISSING_COMPLETION_EVIDENCE",
        "severity": "MEDIUM",
        "weight": 10,
        "description": "Work marked completed without photographic or documentary evidence",
        "action": "Request site photo / completion certificate evidence"
    }
}
