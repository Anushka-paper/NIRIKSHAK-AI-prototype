import pandas as pd
from dateutil import parser
import logging

logger = logging.getLogger(__name__)

def standardize_date(date_str: str):
    """
    Standardizes various Indian date formats (DD/MM/YYYY, DD-MM-YYYY) 
    to Python datetime object for DB insertion. Returns None if unparseable.
    """
    if pd.isna(date_str) or not str(date_str).strip():
        return None
        
    try:
        # dateutil parser with dayfirst=True is ideal for Indian dates
        dt = parser.parse(str(date_str), dayfirst=True)
        return dt
    except Exception as e:
        logger.warning(f"Could not parse date '{date_str}': {e}")
        return None
