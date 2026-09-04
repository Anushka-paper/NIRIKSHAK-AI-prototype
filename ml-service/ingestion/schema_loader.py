"""
Stage 0 — RAW INGESTION (per dataset, per house LS/RS)
Ingests all 6 raw datasets separately without merging.
Preserves source columns as-is (work_id_raw, raw headers) for audit trail.
Partitions by: house -> dataset_name.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Stage0-RawIngestion")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

# Canonical raw dataset mapping based on actual filenames across Lok Sabha and Rajya Sabha
DATASET_PATTERNS = {
    "allocation": ["*allocat*"],
    "recommended": ["*recommend*"],
    "sanctioned": ["*sanction*"],
    "expenditure": ["*expenditure*"],
    "completed": ["*works completed*", "completed.csv"],
    "calamity": ["*calamity*"]
}

def load_raw_csv_safely(file_path: Path) -> pd.DataFrame:
    """
    Loads raw CSV preserving encodings and raw header casing.
    """
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            df = pd.read_csv(
                file_path,
                encoding=enc,
                skipinitialspace=True,
                low_memory=False,
                dtype=str # Retain raw strings to preserve original values exactly
            )
            # Retain original headers stripped of bounding whitespace
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except Exception:
            continue
    raise ValueError(f"Unable to read CSV file across supported encodings: {file_path}")

def ingest_raw_datasets(parliament: str = "lok_sabha", base_raw_dir: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """
    Discovers and loads all 6 datasets for a specified house without premature merging.
    Returns:
      {
         "allocation": {"df": pd.DataFrame, "source_file": Path, "dataset_type": "allocation", "records": int},
         "recommended": {...},
         "sanctioned": {...},
         "expenditure": {...},
         "completed": {...},
         "calamity": {...}
      }
    """
    raw_base = base_raw_dir or (RAW_DIR / parliament)
    if not raw_base.exists():
        logger.warning(f"Raw directory for {parliament} does not exist at {raw_base}")
        return {}

    ingested = {}
    csv_files = list(raw_base.glob("*.csv"))

    for ds_type, patterns in DATASET_PATTERNS.items():
        matched_file = None
        for pat in patterns:
            matches = [
                f for f in csv_files 
                if f.match(pat) and "standardized" not in f.name and "report" not in f.name
            ]
            if matches:
                matched_file = matches[0]
                break

        if matched_file:
            try:
                df = load_raw_csv_safely(matched_file)
                # Ensure work_id_raw is captured if Work/Work ID is present
                work_col = next((c for c in df.columns if c.lower() in ["work", "work id", "work_id", "work id "]), None)
                if work_col:
                    df["work_id_raw"] = df[work_col].copy()

                df["source_house"] = parliament
                df["source_file"] = matched_file.name

                ingested[ds_type] = {
                    "dataset_type": ds_type,
                    "source_file": str(matched_file),
                    "file_name": matched_file.name,
                    "records": len(df),
                    "columns": list(df.columns),
                    "df": df
                }
                logger.info(f"[{parliament.upper()}] Ingested {ds_type}: {len(df)} records from {matched_file.name}")
            except Exception as e:
                logger.error(f"[{parliament.upper()}] Failed to ingest {ds_type} ({matched_file}): {e}")
        else:
            logger.warning(f"[{parliament.upper()}] No raw file found for {ds_type} matching {patterns}")

    return ingested

if __name__ == "__main__":
    for house in ["lok_sabha", "rajya_sabha"]:
        res = ingest_raw_datasets(house)
        print(f"[{house}] Ingested {len(res)} of 6 datasets: {list(res.keys())}")
