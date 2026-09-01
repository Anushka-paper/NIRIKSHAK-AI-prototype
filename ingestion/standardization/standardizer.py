import os
import sys
import re
import pandas as pd
from datetime import datetime
from dateutil import parser
import logging

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "backend/app"))

logger = logging.getLogger(__name__)

# Canonical Category Taxonomy Rules
CATEGORY_TAXONOMY_MAP = [
    (r'(?i)(road|bridge|culvert|path|footpath|tar|pavement|highway|street|lane)', 'Roads / Bridges / Transportation'),
    (r'(?i)(water|tube\s*well|hand\s*pump|sanitation|drain|sewage|toilet|washroom|swachh)', 'Drinking Water / Sanitation'),
    (r'(?i)(school|college|education|library|classroom|blackboard|study|hostel|computer\s*lab)', 'Education / Schools / Libraries'),
    (r'(?i)(hospital|health|dispensary|clinic|ambulance|medical|phc|chc|patient)', 'Health / Medical Infrastructure'),
    (r'(?i)(community|hall|kalyan|auditorium|bhavan|shelter|stage|stadium|sports|playground)', 'Community Infrastructure / Halls'),
    (r'(?i)(solar|electric|light|power|generator|transformer|energy)', 'Electricity / Renewable Energy'),
    (r'(?i)(park|tree|irrigation|canal|pond|lake|boundry|fence|wall)', 'Environment / Parks / Irrigation'),
]

class DataStandardizer:
    """
    NIRIKSHAK AI Canonical Data Standardisation Engine.
    Standardises Dates (ISO-8601), Currency (Numeric ₹ & Cr), and Category Vocabulary.
    """

    @staticmethod
    def standardize_date_iso(date_input: str | datetime | pd.Timestamp) -> str | None:
        """Standardises any input date format to canonical ISO-8601 (YYYY-MM-DD)."""
        if pd.isna(date_input) or date_input is None or not str(date_input).strip():
            return None

        if isinstance(date_input, (datetime, pd.Timestamp)):
            return date_input.strftime('%Y-%m-%d')

        s = str(date_input).strip()
        try:
            dt = parser.parse(s, dayfirst=True)
            return dt.strftime('%Y-%m-%d')
        except Exception as e:
            logger.warning(f"Unparseable date '{s}': {e}")
            return None

    @staticmethod
    def standardize_currency(amount_input: str | float | int) -> dict:
        """
        Standardises currency inputs into canonical numeric float Rupees (₹),
        Crores (Cr), and integer Paise.
        """
        if pd.isna(amount_input) or amount_input is None:
            return {"rupees": 0.0, "crores": 0.0, "paise": 0}

        if isinstance(amount_input, (int, float)):
            val = float(amount_input)
            return {
                "rupees": round(val, 2),
                "crores": round(val / 10000000.0, 6),
                "paise": int(val * 100)
            }

        s = str(amount_input).upper().strip()
        multiplier = 1.0

        if 'CRORE' in s or 'CR' in s:
            multiplier = 10000000.0
        elif 'LAKH' in s or 'L' in s.split():
            multiplier = 100000.0

        numeric_str = re.sub(r'[^\d.]', '', s)
        if not numeric_str:
            return {"rupees": 0.0, "crores": 0.0, "paise": 0}

        try:
            val_rupees = float(numeric_str) * multiplier
            return {
                "rupees": round(val_rupees, 2),
                "crores": round(val_rupees / 10000000.0, 6),
                "paise": int(val_rupees * 100)
            }
        except ValueError:
            return {"rupees": 0.0, "crores": 0.0, "paise": 0}

    @staticmethod
    def standardize_category(raw_category: str) -> str:
        """Maps free-text category strings into canonical category taxonomy."""
        if pd.isna(raw_category) or not str(raw_category).strip():
            return "Other Public Infrastructure"

        clean_cat = str(raw_category).strip()

        for pattern, canonical in CATEGORY_TAXONOMY_MAP:
            if re.search(pattern, clean_cat):
                return canonical

        return "Other Public Infrastructure"

def run_standardization_pipeline(db_session=None):
    """Runs data standardisation across both Lok Sabha and Rajya Sabha records."""
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import WorkRecommended

    session = db_session or SessionLocal()
    standardizer = DataStandardizer()

    stats = {
        "lok_sabha_works": 0,
        "rajya_sabha_works": 0,
        "total_dates_processed": 0,
        "total_currency_amounts_processed": 0,
        "total_categories_standardized": 0
    }

    try:
        works = session.query(WorkRecommended).limit(5000).all()
        for w in works:
            if w.house == "Rajya Sabha":
                stats["rajya_sabha_works"] += 1
            else:
                stats["lok_sabha_works"] += 1

            if w.category:
                w.category = standardizer.standardize_category(w.category)
                stats["total_categories_standardized"] += 1

            if w.recommendation_date:
                iso_date = standardizer.standardize_date_iso(w.recommendation_date)
                if iso_date:
                    w.recommendation_date = iso_date
                    stats["total_dates_processed"] += 1

            if w.recommended_amount:
                curr = standardizer.standardize_currency(w.recommended_amount)
                w.recommended_amount = curr["rupees"]
                stats["total_currency_amounts_processed"] += 1

        session.commit()
        print(f"[Standardisation Complete]: Processed {stats['lok_sabha_works']} Lok Sabha works & "
              f"{stats['rajya_sabha_works']} Rajya Sabha works ({stats['total_dates_processed']} dates, "
              f"{stats['total_currency_amounts_processed']} amounts, "
              f"{stats['total_categories_standardized']} categories).")
        return stats

    except Exception as e:
        session.rollback()
        print(f"[Standardisation Error]: {e}")
        return stats
    finally:
        session.close()

if __name__ == "__main__":
    run_standardization_pipeline()
