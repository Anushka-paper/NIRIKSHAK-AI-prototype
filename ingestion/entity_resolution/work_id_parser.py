import re

def parse_work_id(raw_work_id: str) -> str:
    """
    Extracts the canonical Work ID from a potentially composite string.
    Expected format: XXX-YYY-YYYY-ZZZZ (e.g., EDU-1-2023-0001)
    """
    if not isinstance(raw_work_id, str):
        return str(raw_work_id)
        
    # Look for the pattern: 3 chars - number - 4 digit year - 4 digit number
    # E.g. EDU-1-2023-0001
    pattern = r'([A-Za-z]{3}-\d{1,3}-\d{4}-\d{4,6})'
    match = re.search(pattern, raw_work_id)
    
    if match:
        return match.group(1).upper()
        
    # Fallback to returning the raw ID cleaned up if pattern not found
    return raw_work_id.strip()
