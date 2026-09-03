"""
Configuration for NIRIKSHAK-AI Dynamic Feature Engineering.
"""

from typing import Dict, Any, List

FEATURE_GROUPS: Dict[str, bool] = {
    "entity": True,
    "financial": True,
    "financial_gap": True,
    "temporal": True,
    "lifecycle_duration": True,
    "lifecycle_chronology": True,
    "lifecycle_status": True,
    "work": True,
    "text": True,
    "geographical": True,
    "mp": True,
    "constituency": True,
    "state": True,
    "vendor": True,
    "payment": True,
    "expenditure": True,
    "expenditure_pattern": True,
    "recommendation": True,
    "sanction": True,
    "completion": True,
    "historical": True,
    "rolling": True,
    "trend": True,
    "concentration": True,
    "duplicate": True,
    "cross_dataset_consistency": True,
    "statistical": True,
    "distribution": True,
    "frequency": True,
    "missingness": True,
    "risk_ready_signals": True,
    "ml_readiness": True,
}

THRESHOLDS: Dict[str, Any] = {
    "high_correlation": 0.90,
    "rare_category_pct": 0.01,
    "amount_change_threshold_pct": 20.0,
    "iqr_multiplier": 1.5,
    "rapid_expenditure_days": 15,
    "long_expenditure_gap_days": 90,
}

# Post-prediction fields that must NEVER be used for prediction at sanction time
POST_SANCTION_LEAKAGE_COLUMNS: List[str] = [
    "completion_date",
    "completion_amount",
    "is_completed",
    "total_execution_days",
    "sanction_to_completion_days",
    "first_expenditure_to_completion_days",
    "recommendation_to_completion_days",
    "completion_after_expenditure_flag",
    "completion_before_sanction_flag",
    "total_expenditure",
    "expenditure_amount",
    "expenditure_transaction_count",
    "last_expenditure_date",
    "expenditure_to_sanction_ratio",
    "unspent_amount",
    "remaining_sanctioned_amount",
    "payment_success_rate",
    "delay_target",
    "cost_overrun_target"
]

