"""
Stage 2 — ENTITY RESOLUTION & CLEANING (per dataset)
- Resolve MP names -> stable mp_id (normalize honorifics/spelling variants).
- Resolve constituency/state -> stable constituency_id.
- Resolve Implementing Authority/IDA names -> stable ida_id.
- Resolve Vendor names -> stable vendor_id (fuzzy matching/deterministic cleaning).
- Parse work_id: trim tabs/whitespace with regex, retain work_id_raw alongside cleaned work_id.
- Parse currency fields: strip symbols/commas, validate non-negative bounds.
- Standardize category/work-type vocabulary across all lifecycle datasets into ONE controlled vocabulary.
"""

import os
import re
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Stage2-EntityCleaning")

# Controlled category taxonomy mapped from raw multi-dataset terms
CONTROLLED_CATEGORY_MAP = {
    # Public spaces / lighting
    r"(?i).*(lighting|light|highmast|solar|street).*": "Lighting & Energy Infrastructure",
    # Roads & Pathways
    r"(?i).*(road|culvert|bridge|pathway|cc road|interlocking|rcc).*": "Roads, Bridges & Pathways",
    # Drinking Water & Sanitation
    r"(?i).*(water|handpump|hand pump|submersible|tanker|borewell|piped|drain|drainage|sewer|toilet|sanitat).*": "Drinking Water & Sanitation",
    # Education & School Infrastructure
    r"(?i).*(school|college|classroom|library|vidyalaya|shala|education).*": "Education & Libraries",
    # Community & Public Facilities
    r"(?i).*(community|hall|bhawan|auditorium|shed|cremation|shamshan|boundary wall|park|public space).*": "Community Centers & Public Halls",
    # Healthcare & Medical Facilities
    r"(?i).*(health|hospital|dispensary|ambulance|clinic|medical).*": "Health & Medical Facilities",
    # Agriculture & Irrigation
    r"(?i).*(irrigation|canal|check dam|pond|talab|well|agriculture).*": "Irrigation & Agriculture",
    # Sports & Recreation
    r"(?i).*(sports|gym|stadium|playground|khel).*": "Sports & Recreation",
    # Disaster & Calamity Support
    r"(?i).*(calamity|disaster|flood|relief|cyclone|drought).*": "Disaster & Emergency Relief"
}

def clean_currency_value(val: Any) -> float:
    """
    Cleans raw monetary strings (strips Rs, ₹, commas, symbols, spaces) into valid non-negative float.
    """
    if pd.isna(val) or val is None:
        return 0.0
    s = str(val).strip()
    if s.lower() in ["", "nan", "null", "none", "-", "?"]:
        return 0.0
    # Strip symbols, commas, non-numeric characters except period
    cleaned = re.sub(r"[^\d.]", "", s)
    try:
        f_val = float(cleaned)
        return max(0.0, f_val)
    except (ValueError, TypeError):
        return 0.0

def clean_work_id(raw_work_id: Any) -> Tuple[str, str]:
    """
    Trims tabs, leading/trailing whitespace, and internal excess spaces using regex.
    Returns (cleaned_work_id, raw_work_id).
    """
    if pd.isna(raw_work_id) or raw_work_id is None:
        return "", ""
    raw_str = str(raw_work_id)
    # Remove tabs, newlines, multiple spaces
    cleaned = re.sub(r"[\t\r\n]+", " ", raw_str).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned, raw_str

def normalize_mp_name(raw_name: Any) -> Tuple[str, str]:
    """
    Normalizes MP name: strips honorifics (Hon'ble, Shri, Smt, Dr, Prof, Adv, etc.)
    Returns (mp_id, clean_name).
    """
    if pd.isna(raw_name) or raw_name is None:
        return "MP_UNKNOWN", "Unknown MP"
    s = str(raw_name).strip()
    if s.lower() in ["", "nan", "none"]:
        return "MP_UNKNOWN", "Unknown MP"
    
    # Strip honorifics
    clean = re.sub(r"(?i)\b(hon'?ble|members? of parliament|shri|smt|dr\.?|prof\.?|adv\.?|km\.?|kumari|kunwar|choudhary|sardar)\b", "", s)
    clean = re.sub(r"\s+", " ", clean).strip().title()
    if not clean:
        clean = s.strip().title()

    # Generate stable mp_id from clean name
    name_hash = hashlib.md5(clean.lower().encode()).hexdigest()[:8].upper()
    mp_id = f"MP_{name_hash}"
    return mp_id, clean

def normalize_constituency(raw_const: Any, state: str = "") -> Tuple[str, str]:
    """
    Normalizes constituency name and produces stable constituency_id.
    """
    if pd.isna(raw_const) or raw_const is None:
        return "CONST_UNKNOWN", "General"
    s = str(raw_const).strip()
    if s.lower() in ["", "nan", "none", "-"]:
        return "CONST_UNKNOWN", "General"
    
    # Clean reserved markers like (SC), (ST)
    clean = re.sub(r"\s+", " ", s).strip().upper()
    state_clean = str(state).strip().upper().replace(" ", "_")[:6] if state else "IN"
    slug = re.sub(r"[^A-Z0-9]", "_", clean)[:16].strip("_")
    const_id = f"C_{state_clean}_{slug}"
    return const_id, clean

def normalize_ida(raw_ida: Any) -> Tuple[str, str]:
    """
    Normalizes Implementing Authority (IDA) name.
    """
    if pd.isna(raw_ida) or raw_ida is None:
        return "IDA_UNKNOWN", "District Authority"
    s = str(raw_ida).strip()
    if s.lower() in ["", "nan", "none", "-"]:
        return "IDA_UNKNOWN", "District Authority"
    clean = re.sub(r"\s+", " ", s).strip().upper()
    ida_hash = hashlib.md5(clean.lower().encode()).hexdigest()[:8].upper()
    return f"IDA_{ida_hash}", clean

def normalize_vendor(raw_vendor: Any) -> Tuple[str, str]:
    """
    Normalizes vendor name and produces stable vendor_id.
    """
    if pd.isna(raw_vendor) or raw_vendor is None:
        return "VEND_UNKNOWN", "Unspecified Vendor"
    s = str(raw_vendor).strip()
    if s.lower() in ["", "nan", "none", "-", "self"]:
        return "VEND_UNKNOWN", "Unspecified Vendor"
    clean = re.sub(r"\s+", " ", s).strip().upper()
    v_hash = hashlib.md5(clean.lower().encode()).hexdigest()[:8].upper()
    return f"VEND_{v_hash}", clean

def map_controlled_category(raw_category: Any, description: str = "") -> str:
    """
    Maps varied category/work-type strings across Recommended, Sanctioned, Expenditure, 
    and Completed to a single controlled vocabulary.
    """
    combined_text = f"{raw_category or ''} {description or ''}".strip().lower()
    for regex_pat, canon_cat in CONTROLLED_CATEGORY_MAP.items():
        if re.match(regex_pat, combined_text):
            return canon_cat
    return "Other Public Infrastructure"

def clean_dataset(df: pd.DataFrame, dataset_type: str, parliament: str = "lok_sabha") -> pd.DataFrame:
    """
    Executes Stage 2 cleaning on a validated dataset.
    """
    df_clean = df.copy()

    # 1. Clean Work ID
    work_col = next((c for c in df_clean.columns if c.lower() in ["work", "work id", "work_id", "work id "]), None)
    if work_col:
        cleaned_pairs = [clean_work_id(x) for x in df_clean[work_col]]
        df_clean["work_id"] = [p[0] for p in cleaned_pairs]
        if "work_id_raw" not in df_clean.columns:
            df_clean["work_id_raw"] = [p[1] for p in cleaned_pairs]

    # 2. Clean MPs
    mp_col = next((c for c in df_clean.columns if "member" in c.lower() or "mp" in c.lower()), None)
    if mp_col:
        mp_pairs = [normalize_mp_name(x) for x in df_clean[mp_col]]
        df_clean["mp_id"] = [p[0] for p in mp_pairs]
        df_clean["mp_name_clean"] = [p[1] for p in mp_pairs]

    # 3. Clean Constituencies & States
    const_col = next((c for c in df_clean.columns if "constituency" in c.lower() or "elected" in c.lower()), None)
    state_col = next((c for c in df_clean.columns if "state" in c.lower()), None)
    
    states = df_clean[state_col] if state_col else [""] * len(df_clean)
    if const_col:
        c_pairs = [normalize_constituency(c, st) for c, st in zip(df_clean[const_col], states)]
        df_clean["constituency_id"] = [p[0] for p in c_pairs]
        df_clean["constituency_clean"] = [p[1] for p in c_pairs]

    # 4. Clean IDAs
    ida_col = next((c for c in df_clean.columns if "ida" in c.lower() or "agency" in c.lower()), None)
    if ida_col:
        ida_pairs = [normalize_ida(x) for x in df_clean[ida_col]]
        df_clean["ida_id"] = [p[0] for p in ida_pairs]
        df_clean["ida_name_clean"] = [p[1] for p in ida_pairs]

    # 5. Clean Vendors
    vendor_col = next((c for c in df_clean.columns if "vendor" in c.lower()), None)
    if vendor_col:
        vend_pairs = [normalize_vendor(x) for x in df_clean[vendor_col]]
        df_clean["vendor_id"] = [p[0] for p in vend_pairs]
        df_clean["vendor_name_clean"] = [p[1] for p in vend_pairs]

    # 6. Clean Currencies
    for col in df_clean.columns:
        if any(w in col.lower() for w in ["amount", "disbursed", "cost", "sanction", "recommended", "consent"]):
            clean_name = f"{col.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('rs', '').strip('_')}_clean"
            df_clean[clean_name] = df_clean[col].apply(clean_currency_value)

    # 7. Standardize Work Category
    cat_col = next((c for c in df_clean.columns if "category" in c.lower()), None)
    desc_col = next((c for c in df_clean.columns if "description" in c.lower() or "work" in c.lower()), None)
    
    cats = df_clean[cat_col] if cat_col else [""] * len(df_clean)
    descs = df_clean[desc_col] if desc_col else [""] * len(df_clean)
    df_clean["canonical_category"] = [map_controlled_category(c, d) for c, d in zip(cats, descs)]

    logger.info(f"[{parliament.upper()}] Cleaned {dataset_type}: {len(df_clean)} rows standardized with canonical IDs & vocabulary.")
    return df_clean
