import re
import pandas as pd

def clean_currency_to_paise(amount_str: str | float | int) -> int:
    """
    Parses various currency formats and converts to integer paise.
    e.g., "₹ 50,000.50", "50000", "50.5 Lakhs", "5 Cr" -> paise
    """
    if pd.isna(amount_str) or amount_str is None:
        return 0
        
    if isinstance(amount_str, (int, float)):
        return int(amount_str * 100)
        
    # Convert to string and uppercase
    s = str(amount_str).upper()
    
    # Remove non-numeric except dot and multiplier words
    # E.g. LAKH, CR, CRORE
    multiplier = 1.0
    if 'LAKH' in s or 'L' in s.split():
        multiplier = 100000.0
    elif 'CRORE' in s or 'CR' in s:
        multiplier = 10000000.0
        
    # Extract just the numbers and decimals
    numeric_str = re.sub(r'[^\d.]', '', s)
    if not numeric_str:
        return 0
        
    try:
        val = float(numeric_str) * multiplier
        return int(val * 100) # to paise
    except ValueError:
        return 0
