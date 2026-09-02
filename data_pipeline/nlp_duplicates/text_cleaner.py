import re
from data_pipeline.nlp_duplicates.config import ABBREVIATIONS_DICT, BOILERPLATE_TERMS

def expand_abbreviations(text: str) -> str:
    """
    Expands common Indian government abbreviations using config dictionary (§9).
    """
    if not text:
        return ""
        
    res = text.lower()
    for pattern, replacement in ABBREVIATIONS_DICT.items():
        res = re.sub(pattern, replacement, res)
    return res

def clean_work_description(text: str) -> str:
    """
    Cleans raw work description text (§9):
    1. Lowercase
    2. Strip boilerplate phrases
    3. Expand abbreviations via config dictionary
    4. Remove excess whitespace & punctuation
    """
    if not text or not isinstance(text, str):
        return ""

    cleaned = text.lower().strip()

    # Strip boilerplate phrases
    for bp in BOILERPLATE_TERMS:
        cleaned = cleaned.replace(bp, " ")

    # Expand abbreviations
    cleaned = expand_abbreviations(cleaned)

    # Remove non-alphanumeric except spaces
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned if cleaned else "infrastructure work"

