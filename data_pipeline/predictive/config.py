RANDOM_STATE = 42
N_ESTIMATORS = 100
DELAY_SANCTION_THRESHOLD = 30.0
DELAY_COMPLETION_THRESHOLD = 90.0
STAGNATION_AGE_THRESHOLD = 180.0

PREDICTIVE_FEATURE_COLS = [
    "sanctioned_amount_inr",
    "recommended_amount_inr",
    "expenditure_amount_inr",
    "sanction_delay_days",
    "completion_delay_days",
    "overrun_pct",
    "estimate_variance_pct",
    "inactivity_gap_days",
    "has_recommendation",
    "has_sanction",
    "has_expenditure"
]
