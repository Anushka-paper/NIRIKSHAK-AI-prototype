import re

def normalize_header(header: str) -> str:
    """
    Normalizes a CSV header to a canonical snake_case format.
    e.g., " Work ID  " -> "work_id", "Recommended Amount (Rs)" -> "recommended_amount"
    """
    if not isinstance(header, str):
        return str(header)
        
    s = header.strip().lower()
    
    # Remove unit parentheticals like (Rs), (In Lakhs)
    s = re.sub(r'\(.*?\)', '', s)
    
    # Replace non-alphanumeric with underscores
    s = re.sub(r'[^a-z0-9]+', '_', s)
    
    # Remove leading/trailing underscores
    s = s.strip('_')
    
    return s
