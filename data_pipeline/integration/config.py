DATASET_GRAIN_CONFIG = {
    "works_recommended": {"grain": "work-level", "primary_key": "canonical_work_id", "confidence": "HIGH"},
    "works_sanctioned": {"grain": "work-level", "primary_key": "canonical_work_id", "confidence": "HIGH"},
    "works_completed": {"grain": "work-level", "primary_key": "canonical_work_id", "confidence": "HIGH"},
    "expenditure": {"grain": "expenditure-transaction-level", "primary_key": "canonical_work_id", "confidence": "HIGH"},
    "allocated_limit": {"grain": "mp-level", "primary_key": "canonical_mp_id", "confidence": "LOW"},
    "calamity_consent": {"grain": "mp-calamity-level", "primary_key": "canonical_mp_id", "confidence": "LOW"}
}
