RULE_CONFIGS = {
    "SCH-001": {"name": "Required Columns Check", "severity": "ERROR", "enabled": True},
    "SCH-002": {"name": "Unexpected Columns Warning", "severity": "WARNING", "enabled": True},
    "TYP-001": {"name": "Numeric Data Type Check", "severity": "ERROR", "enabled": True},
    "TYP-002": {"name": "ISO Date Format Check", "severity": "ERROR", "enabled": True},
    "NUL-001": {"name": "Required Field Completeness", "severity": "ERROR", "enabled": True},
    "NUL-002": {"name": "Conditional Field Completeness", "severity": "WARNING", "enabled": True},
    "ID-001":  {"name": "Work ID Format Validation", "severity": "WARNING", "enabled": True},
    "CUR-001": {"name": "Non-Negative Currency", "severity": "ERROR", "enabled": True},
    "CUR-002": {"name": "Suspicious Large Amount Warning", "severity": "WARNING", "enabled": True},
    "CUR-003": {"name": "Disbursement Limit Check", "severity": "WARNING", "enabled": True},
    "DAT-001": {"name": "Chronological Sequence Check", "severity": "ERROR", "enabled": True},
    "DAT-002": {"name": "Date Gap Warning", "severity": "WARNING", "enabled": True},
    "REF-001": {"name": "Expenditure Work ID Reference Integrity", "severity": "WARNING", "enabled": True},
    "GEO-001": {"name": "Geographic Attribute Verification", "severity": "INFO", "enabled": True},
    "BUS-001": {"name": "Completed Status Work Check", "severity": "WARNING", "enabled": True},
    "HOU-001": {"name": "Source House Lineage Validation", "severity": "ERROR", "enabled": True}
}
