"""
Field Normalization Utilities for Entity Resolution.
Normalizes text, MP names, honorifics, constituencies, and amounts without destroying information.
"""

import re
import unicodedata

# Honorifics pattern
HONORIFICS_PATTERN = r'(?i)\b(shri|smt|dr\.?|mr\.?|mrs\.?|ms\.?|prof\.?|hon\'?ble|honble|adv\.?|thiru|km|kumar|kumari)\b\.?'

def normalize_text(val) -> str:
    """
    Normalizes generic text: unicode NFKC, lowercase, collapse whitespace, strip punctuation noise.
    """
    if val is None or (isinstance(val, float) and str(val) == 'nan'):
        return ""
    s = unicodedata.normalize('NFKC', str(val))
    s = s.lower()
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def normalize_mp_name(val) -> str:
    """
    Normalizes MP/Person names by stripping honorifics, extra spaces, and special symbols.
    e.g. "Hon'ble Shri Ram Singh" -> "ram singh"
    """
    if val is None or (isinstance(val, float) and str(val) == 'nan'):
        return ""
    s = unicodedata.normalize('NFKC', str(val))
    # Strip honorifics
    s = re.sub(HONORIFICS_PATTERN, ' ', s)
    s = s.lower()
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def normalize_constituency(val) -> str:
    """
    Normalizes constituency names, stripping parenthetical state abbreviations or reservation codes (SC/ST).
    e.g. "Lucknow (U.P.)" -> "lucknow", "FARIDKOT(SC)" -> "faridkot"
    """
    if val is None or (isinstance(val, float) and str(val) == 'nan'):
        return ""
    s = unicodedata.normalize('NFKC', str(val))
    s = re.sub(r'\([^\)]*\)', ' ', s)  # Remove parentheticals
    s = s.lower()
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def normalize_work_id(val) -> str:
    """
    Standardizes official work ID strings, preserving exact alphanumeric code without spaces.
    e.g. " WS/MP18086/2026-2027/292888 " -> "WS/MP18086/2026-2027/292888"
    """
    if val is None or (isinstance(val, float) and str(val) == 'nan'):
        return ""
    s = str(val).strip()
    return s.upper()

def normalize_amount_to_float(val) -> float | None:
    """
    Converts amount value to numeric float safely.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val) if not str(val) == 'nan' else None
    try:
        s = str(val).replace(',', '').strip()
        nums = re.sub(r'[^\d.]', '', s)
        return float(nums) if nums else None
    except Exception:
        return None

