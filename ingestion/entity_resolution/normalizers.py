import re
import unicodedata

# Honorifics and titles regex patterns
HONORIFICS_PATTERN = r'(?i)\b(shri|smt|dr|prof|hon\'ble|mr|mrs|ms|ji|sh|er|adv)\.?\s*'

# Common company & agency suffix normalization maps
VENDOR_SUFFIX_MAP = [
    (r'(?i)\bpvt\.?\s*ltd\.?\b', 'Private Limited'),
    (r'(?i)\bco\.?\s*ltd\.?\b', 'Company Limited'),
    (r'(?i)\binc\.?\b', 'Incorporated'),
    (r'(?i)\bcorp\.?\b', 'Corporation'),
    (r'(?i)\bconst\.?\b', 'Construction'),
    (r'(?i)\bm/s\.?\b', ''),
    (r'(?i)\b& co\.?\b', 'And Company'),
]

IDA_SUFFIX_MAP = [
    (r'(?i)\bp\.?w\.?d\.?\b', 'Public Works Department'),
    (r'(?i)\bdiv\.?\b', 'Division'),
    (r'(?i)\bdept\.?\b', 'Department'),
    (r'(?i)\bexe\.?\s*eng\.?\b', 'Executive Engineer'),
]

def normalize_text(text: str, entity_type: str = "generic") -> dict:
    """
    Deterministic Entity Normalisation Function.
    Handles Unicode normalization, lowercase, whitespace collapse,
    honorific stripping, and abbreviation expansion.
    Returns a dict with both original_value and normalized_value.
    """
    if not text or not str(text).strip():
        return {
            "original_value": "" if text is None else str(text),
            "normalized_value": ""
        }

    raw_val = str(text).strip()
    
    # 1. Unicode Normalization (NFKD)
    normalized = unicodedata.normalize('NFKD', raw_val)
    normalized = normalized.encode('ASCII', 'ignore').decode('utf-8')
    
    # 2. Lowercase conversion
    normalized = normalized.lower()

    # 3. Entity-specific transformations
    if entity_type == "mp":
        normalized = re.sub(HONORIFICS_PATTERN, '', normalized)
    elif entity_type == "vendor":
        normalized = re.sub(HONORIFICS_PATTERN, '', normalized)
        for pattern, replacement in VENDOR_SUFFIX_MAP:
            normalized = re.sub(pattern, replacement.lower(), normalized)
    elif entity_type == "ida":
        for pattern, replacement in IDA_SUFFIX_MAP:
            normalized = re.sub(pattern, replacement.lower(), normalized)

    # 4. Remove special punctuation (preserve spaces & alphanumerics)
    normalized = re.sub(r'[^\w\s]', ' ', normalized)

    # 5. Collapse repeated whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    return {
        "original_value": raw_val,
        "normalized_value": normalized
    }

