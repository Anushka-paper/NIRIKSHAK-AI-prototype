import re
import pandas as pd
from .rules import COLUMN_NAME_SYNONYM_MAP

def normalize_column_name(raw_name: str) -> str:
    """
    Standardises raw column header to canonical snake_case.
    e.g. 'Hon'ble Members of Parliaments' -> 'mp_name', 'Allocated AMOUNT ( ₹ )' -> 'allocated_amount'
    """
    clean_name = str(raw_name).strip()

    # Match against synonym regex patterns
    for pattern, canonical in COLUMN_NAME_SYNONYM_MAP.items():
        if re.search(pattern, clean_name):
            return canonical

    # Generic snake_case fallback for unknown columns
    s = re.sub(r'[^\w\s]', '', clean_name)
    s = re.sub(r'\s+', '_', s).strip('_').lower()
    return s if s else "unnamed_column"

def detect_column_rule_type(col_name: str, series: pd.Series, profile_info: dict = None) -> str:
    """
    Determines standardisation rule type (state, currency, date, identifier, name, category, etc.)
    using normalized column name and value characteristics.
    """
    col_norm = normalize_column_name(col_name)

    # 1. Column Name Explicit Semantic Overrides
    if col_norm == 'state':
        return 'state'
    if col_norm in ['mp_name', 'vendor_name']:
        return 'person_name'
    if col_norm in ['allocated_amount', 'recommended_amount', 'sanction_amount', 'expenditure_amount']:
        return 'currency'
    if col_norm in ['recommended_date', 'sanction_date', 'completion_date', 'expenditure_date']:
        return 'date'
    if col_norm in ['work_id', 'sr_no']:
        return 'identifier'
    if col_norm in ['work_category', 'calamity_type', 'calamity_name']:
        return 'category'
    if col_norm in ['work_status', 'payment_status']:
        return 'status'

    # 2. Value-based Fallback Detection
    non_null = series.dropna().astype(str).str.strip()
    if non_null.empty:
        return 'text'

    if any(k in col_norm for k in ['date', 'day', 'time', 'dt']):
        return 'date'

    if any(k in col_norm for k in ['amount', 'cost', 'fund', 'budget', 'expenditure']):
        return 'currency'

    if any(k in col_norm for k in ['id', 'code', 'no']):
        return 'identifier'

    unique_lower = set(non_null.str.lower().unique())
    if unique_lower.issubset({'true', 'false', 'yes', 'no', 'y', 'n', '0', '1'}):
        return 'boolean'

    return 'text'
