"""
Stage 1 — SCHEMA VALIDATION & QUARANTINE (per dataset)
Robust character-agnostic validator for required fields per dataset grain.
Handles currency symbol variations (₹, Rs, (  ), etc.).
Routes invalid rows to data/quarantine/{parliament}/{dataset}_quarantine.csv instead of silently dropping.
"""

import os
import re
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Stage1-SchemaValidation")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"

# Keywords used to match required concepts regardless of symbol encodings
REQUIRED_PATTERNS = {
    "allocation": {
        "mp": [r"member", r"mp\s*name"],
        "amount": [r"allocat.*amount"]
    },
    "recommended": {
        "work": [r"^work$", r"^work\s*id$"],
        "date": [r"recommend.*date"],
        "amount": [r"recommend.*amount"]
    },
    "sanctioned": {
        "work": [r"^work$", r"^work\s*id$"],
        "date": [r"sanction.*date"],
        "amount": [r"sanction.*amount"]
    },
    "expenditure": {
        "work": [r"^work$", r"^work\s*id$"],
        "amount": [r"disburs.*amount", r"expenditure.*amount"]
    },
    "completed": {
        "work": [r"^work$", r"^work\s*id$"],
        "date": [r"completion.*date"],
        "amount": [r"disburs.*amount", r"amount.*disburs"]
    },
    "calamity": {
        "mp": [r"member", r"mp\s*name"],
        "amount": [r"consent.*amount"]
    }
}

AMBIGUOUS_COLUMNS = [
    "Additional Date/Status Field",
    "Sanction Date",
    "Image",
    "Work Status",
    "Payment Status"
]

def find_matching_column(columns: List[str], regex_patterns: List[str]) -> str:
    """Find column matching any of the regex patterns (case-insensitive, unicode-safe)."""
    for col in columns:
        col_clean = re.sub(r"[^\w\s]", " ", col).lower()
        for pat in regex_patterns:
            if re.search(pat, col_clean) or re.search(pat, col.lower()):
                return col
    return ""

def validate_and_quarantine(
    df: pd.DataFrame, 
    dataset_type: str, 
    parliament: str = "lok_sabha",
    quarantine_base: Path = None
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    q_dir = quarantine_base or (QUARANTINE_DIR / parliament)
    q_dir.mkdir(parents=True, exist_ok=True)

    spec = REQUIRED_PATTERNS.get(dataset_type)
    if not spec:
        return df, pd.DataFrame(), {"status": "unconstrained", "quarantined_count": 0}

    valid_mask = pd.Series(True, index=df.index)
    failure_reasons = pd.Series("", index=df.index)

    matched_cols = {}
    missing_required = []

    for req_concept, patterns in spec.items():
        found = find_matching_column(list(df.columns), patterns)
        if found:
            matched_cols[req_concept] = found
        else:
            missing_required.append(req_concept)

    if missing_required:
        logger.error(f"[{parliament.upper()}] {dataset_type} missing required column concepts: {missing_required}")
        failure_reasons += f"Missing structural column concepts: {missing_required}; "
        valid_mask = pd.Series(False, index=df.index)
    else:
        # Check null/empty on required fields
        for req_concept, col_name in matched_cols.items():
            is_empty = df[col_name].isna() | (df[col_name].astype(str).str.strip().isin(["", "nan", "None", "NULL", "-"]))
            if is_empty.any():
                valid_mask = valid_mask & (~is_empty)
                failure_reasons[is_empty] += f"Missing required value in '{col_name}'; "

    ambiguous_present = [c for c in df.columns if any(amb.lower() in c.lower() for amb in AMBIGUOUS_COLUMNS)]

    valid_df = df[valid_mask].copy()
    quarantined_df = df[~valid_mask].copy()

    if not quarantined_df.empty:
        quarantined_df["quarantine_reason"] = failure_reasons[~valid_mask]
        quarantine_file = q_dir / f"{dataset_type}_quarantine.csv"
        quarantined_df.to_csv(quarantine_file, index=False)
        logger.warning(f"[{parliament.upper()}] Quarantined {len(quarantined_df)} rows from {dataset_type} -> {quarantine_file.name}")
    else:
        logger.info(f"[{parliament.upper()}] All {len(valid_df)} rows in {dataset_type} passed schema validation.")

    report = {
        "dataset_type": dataset_type,
        "parliament": parliament,
        "total_rows": len(df),
        "valid_rows": len(valid_df),
        "quarantined_rows": len(quarantined_df),
        "matched_critical_columns": matched_cols,
        "ambiguous_columns_flagged": ambiguous_present,
        "validation_passed": len(quarantined_df) == 0
    }

    return valid_df, quarantined_df, report
