import re
import unicodedata
import pandas as pd
import numpy as np
from dateutil import parser
from datetime import datetime
from .rules import (
    STATE_CANONICAL_MAPPING,
    MISSING_VALUE_TOKENS,
    PERSON_HONORIFICS,
    STATUS_CANONICAL_MAPPING,
    CATEGORY_VOCABULARY
)

def is_missing_value(val) -> bool:
    """Checks if a value represents a missing/null token."""
    if pd.isna(val) or val is None:
        return True
    s = str(val).strip().lower()
    return s in MISSING_VALUE_TOKENS

def clean_text(val) -> str | None:
    """Trims whitespace, normalizes unicode, and cleans multiple spaces."""
    if is_missing_value(val):
        return None
    s = unicodedata.normalize('NFKC', str(val))
    s = re.sub(r'\s+', ' ', s).strip()
    return s if s else None

def standardize_state_value(val) -> tuple[str | None, bool]:
    """
    Standardises state string against Indian States & UTs canonical vocabulary.
    Returns (standardized_state, was_changed).
    """
    if is_missing_value(val):
        return None, False

    clean_raw = str(val).strip()
    key_lower = clean_raw.lower().replace('.', '').replace('_', ' ')
    key_lower = re.sub(r'\s+', ' ', key_lower).strip()

    if key_lower in STATE_CANONICAL_MAPPING:
        canonical = STATE_CANONICAL_MAPPING[key_lower]
        return canonical, (clean_raw != canonical)

    fallback = clean_raw.title()
    return fallback, (clean_raw != fallback)

def standardize_currency_value(val) -> tuple[float | None, bool]:
    """
    Standardises monetary string (₹ 10,00,000, Rs. 5,00,000, 10 Lakh) into numeric float.
    Removes currency labels like 'Rs.', 'INR', '₹' before float extraction.
    Returns (numeric_float, was_changed).
    """
    if is_missing_value(val):
        return None, False

    raw_str = str(val).strip()
    s_upper = raw_str.upper()
    multiplier = 1.0

    if 'CRORE' in s_upper or 'CR' in s_upper:
        multiplier = 10000000.0
    elif 'LAKH' in s_upper or 'L' in s_upper.split():
        multiplier = 100000.0

    s_clean = re.sub(r'(?i)(rs\.?|inr|₹|\$|€|£)', '', raw_str)
    s_clean = s_clean.replace(',', '').strip()

    nums = re.sub(r'[^\d.]', '', s_clean)
    if not nums:
        return None, False

    try:
        parts = nums.split('.')
        if len(parts) > 2:
            nums = parts[0] + '.' + ''.join(parts[1:])
        numeric_val = round(float(nums) * multiplier, 2)
        return numeric_val, True
    except ValueError:
        return None, False

def standardize_date_iso(val) -> tuple[str | None, bool]:
    """
    Standardises date string to ISO-8601 YYYY-MM-DD.
    If date starts with 4-digit year (YYYY-MM-DD), parses without dayfirst.
    Otherwise uses dayfirst=True for Indian date format conventions (DD/MM/YYYY).
    Returns (iso_date_str, was_changed).
    """
    if is_missing_value(val):
        return None, False

    raw_str = str(val).strip()

    if re.match(r'^\d{4}[-/.]', raw_str):
        try:
            dt = parser.parse(raw_str, dayfirst=False)
            iso_str = dt.strftime('%Y-%m-%d')
            return iso_str, (raw_str != iso_str)
        except Exception:
            pass

    try:
        dt = parser.parse(raw_str, dayfirst=True)
        iso_str = dt.strftime('%Y-%m-%d')
        return iso_str, (raw_str != iso_str)
    except Exception:
        return None, False

def standardize_person_name(val) -> tuple[str | None, bool]:
    """
    Standardises person name: trims honorifics (Shri, Smt, Dr.), extra spaces, and formats title case.
    """
    if is_missing_value(val):
        return None, False

    raw_str = str(val).strip()
    honorific_pattern = r'(?i)\b(shri|smt|dr\.?|mr\.?|mrs\.?|ms\.?|prof\.?|hon\'ble|honble|adv\.?)\b\.?'
    cleaned = re.sub(honorific_pattern, '', raw_str).strip()
    cleaned = re.sub(r'^[.\s]+', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip().title()

    return cleaned, (raw_str != cleaned)

def standardize_identifier_string(val) -> tuple[str | None, bool]:
    """
    Preserves identifier strictly as string. Trims spaces, keeps leading zeros.
    """
    if is_missing_value(val):
        return None, False

    raw_str = str(val).strip()
    return raw_str, False

def standardize_boolean_value(val) -> tuple[bool | None, bool]:
    """Standardises boolean representation."""
    if is_missing_value(val):
        return None, False

    s = str(val).strip().lower()
    if s in {'true', 'yes', 'y', '1'}:
        return True, True
    if s in {'false', 'no', 'n', '0'}:
        return False, True

    return None, False

def standardize_status_value(val) -> tuple[str | None, bool]:
    """Standardises status values against taxonomy."""
    if is_missing_value(val):
        return None, False

    raw_str = str(val).strip()
    s_lower = raw_str.lower()

    if s_lower in STATUS_CANONICAL_MAPPING:
        canonical = STATUS_CANONICAL_MAPPING[s_lower]
        return canonical, (raw_str != canonical)

    title_val = raw_str.title()
    return title_val, (raw_str != title_val)

def standardize_category_vocabulary(val) -> tuple[str | None, bool]:
    """Standardises work category against vocabulary."""
    if is_missing_value(val):
        return "Other Public Infrastructure", False

    raw_str = str(val).strip()
    for pattern, canonical in CATEGORY_VOCABULARY:
        if re.search(pattern, raw_str):
            return canonical, (raw_str != canonical)

    title_val = raw_str.title()
    return title_val, (raw_str != title_val)
