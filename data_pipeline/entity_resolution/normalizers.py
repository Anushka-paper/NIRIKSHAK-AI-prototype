import re

HONORIFICS_REGEX = r'^(SHRI|SMT|DR\.?|PROF\.?|ADV\.?|HONABLE|HON\'BLE|SH\.|SHRI\.)\s+'

VENDOR_ABBREVIATIONS = {
    r'\bPVT\.?\b': 'PRIVATE',
    r'\bLTD\.?\b': 'LIMITED',
    r'\bCONST\.?\b': 'CONSTRUCTION',
    r'\bDEPT\.?\b': 'DEPARTMENT',
    r'\bCORP\.?\b': 'CORPORATION',
    r'\bENGG\.?\b': 'ENGINEERING'
}

def normalize_name(val):
    if not isinstance(val, str) or not val.strip():
        return "unknown_entity"
    v = val.strip().upper()
    v = re.sub(HONORIFICS_REGEX, '', v)
    v = re.sub(r'[^A-Z0-9\s]', '', v)
    v = ' '.join(v.split())
    return v.lower()

def normalize_vendor(val):
    if not isinstance(val, str) or not val.strip():
        return "unknown_vendor"
    v = val.strip().upper()
    for pattern, repl in VENDOR_ABBREVIATIONS.items():
        v = re.sub(pattern, repl, v)
    v = re.sub(r'[^A-Z0-9\s]', '', v)
    v = ' '.join(v.split())
    return v.lower()

def normalize_ida(val):
    if not isinstance(val, str) or not val.strip():
        return "unknown_ida"
    v = val.strip().upper()
    v = v.replace("P.W.D.", "PUBLIC WORKS DEPARTMENT").replace("PWD", "PUBLIC WORKS DEPARTMENT")
    v = re.sub(r'[^A-Z0-9\s]', '', v)
    v = ' '.join(v.split())
    return v.lower()
