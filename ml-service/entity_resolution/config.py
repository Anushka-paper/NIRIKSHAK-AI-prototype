"""
Configuration for Dynamic Entity Resolution Engine.
"""

# Confidence Thresholds
HIGH_CONFIDENCE_THRESHOLD = 85.0
MEDIUM_CONFIDENCE_THRESHOLD = 65.0

# Tolerance Parameters
AMOUNT_TOLERANCE_PCT = 0.15      # Up to 15% difference in amount is tolerated
AMOUNT_EXACT_TOLERANCE = 100.0    # Absolute difference threshold in INR
DATE_CHRONOLOGY_PENALTY = 20.0    # Penalty if chronology is reversed (e.g. sanction before recommendation)

# Default Multi-Field Weights (dynamically normalized based on present columns)
DEFAULT_FIELD_WEIGHTS = {
    "work_id": 0.40,
    "work_description": 0.20,
    "mp_name": 0.15,
    "constituency": 0.10,
    "amount": 0.05,
    "date": 0.05,
    "state": 0.03,
    "ida_agency": 0.02
}

# Semantic Column Aliases (Lowercase normalized regex or substrings)
SEMANTIC_COLUMN_ALIASES = {
    "work_id": [
        r'(?i)^(work\s*id|project\s*id|work_id|application\s*id|workid)$',
        r'(?i)\bwork_id\b'
    ],
    "mp_name": [
        r'(?i)^(hon\'?ble\s+members?\s+of\s+parliaments?|mp\s*name|parliamentarian|mp|member)$',
        r'(?i)\bmp_name\b'
    ],
    "state": [
        r'(?i)^state$',
        r'(?i)\bstate\b'
    ],
    "constituency": [
        r'(?i)^(constituency|nodal\s+district|district)$',
        r'(?i)\bconstituency\b'
    ],
    "work_description": [
        r'(?i)^(work\s+description|description|project\s+details|work|work_details)$',
        r'(?i)\bwork_description\b'
    ],
    "work_category": [
        r'(?i)^(work\s+category|category)$',
        r'(?i)\bwork_category\b'
    ],
    "amount": [
        r'(?i)^(allocated\s+amount.*|recommended\s+amount.*|sanction\s+amount.*|sanctioned\s+amount.*|fund\s+disbursed.*|expenditure\s+amount.*|amount)$',
        r'(?i)\bamount\b'
    ],
    "recommendation_date": [
        r'(?i)^(recommended\s+date|recommendation\s+date)$',
        r'(?i)\brecommended_date\b'
    ],
    "sanction_date": [
        r'(?i)^(sanction\s+date|sanctioned\s+date)$',
        r'(?i)\bsanction_date\b'
    ],
    "completion_date": [
        r'(?i)^(completion\s+date|completed\s+date)$',
        r'(?i)\bcompletion_date\b'
    ],
    "expenditure_date": [
        r'(?i)^(expenditure\s+date|payment\s+date)$',
        r'(?i)\bexpenditure_date\b'
    ],
    "ida_agency": [
        r'(?i)^(ida|implementing\s+agency|agency|ida_agency)$',
        r'(?i)\bida_agency\b'
    ],
    "vendor_name": [
        r'(?i)^(vendor\s+name|vendor)$',
        r'(?i)\bvendor_name\b'
    ],
    "work_status": [
        r'(?i)^(work\s+status|status|payment\s+status)$',
        r'(?i)\bwork_status\b'
    ]
}

# Candidate Blocking Keys
BLOCKING_KEYS = [
    ["state", "constituency"],
    ["state", "mp_name"],
    ["mp_name", "constituency"]
]

# Datasets to exclude from direct work-level resolution
SPECIAL_DATASET_TYPES = {
    "allocation": "aggregate_level",
    "calamity": "emergency_stream"
}

