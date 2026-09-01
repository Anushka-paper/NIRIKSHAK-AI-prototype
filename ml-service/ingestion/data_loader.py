import os
import sys
import logging
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_RAW_DIR = BASE_DIR / "data" / "raw"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DataLoader")

def discover_datasets(base_dir: str | Path = None, parliament: str = "all") -> dict[str, list[Path]]:
    """
    Dynamically scans data/raw/ subdirectories for Lok Sabha and Rajya Sabha CSV/Excel datasets.
    Returns dict mapping parliament ('lok_sabha', 'rajya_sabha') to list of file Paths.
    """
    raw_path = Path(base_dir) if base_dir else DEFAULT_RAW_DIR
    if not raw_path.exists():
        logger.warning(f"Raw data directory does not exist: {raw_path}")
        return {"lok_sabha": [], "rajya_sabha": []}

    discovered = {"lok_sabha": [], "rajya_sabha": []}

    # 1. Check lok_sabha subdirectory
    ls_dir = raw_path / "lok_sabha"
    if ls_dir.exists() and ls_dir.is_dir():
        discovered["lok_sabha"].extend(sorted([f for f in ls_dir.glob("*.csv") if f.is_file()]))
        discovered["lok_sabha"].extend(sorted([f for f in ls_dir.glob("*.xlsx") if f.is_file()]))

    # If no files in lok_sabha subfolder, fallback to checking root raw_path for legacy LS files
    if not discovered["lok_sabha"]:
        root_csvs = [f for f in raw_path.glob("*.csv") if f.is_file()]
        if root_csvs:
            discovered["lok_sabha"].extend(sorted(root_csvs))

    # 2. Check rajya_sabha subdirectory
    rs_dir = raw_path / "rajya_sabha"
    if rs_dir.exists() and rs_dir.is_dir():
        discovered["rajya_sabha"].extend(sorted([f for f in rs_dir.glob("*.csv") if f.is_file()]))
        discovered["rajya_sabha"].extend(sorted([f for f in rs_dir.glob("*.xlsx") if f.is_file()]))

    if parliament == "lok_sabha":
        return {"lok_sabha": discovered["lok_sabha"]}
    elif parliament == "rajya_sabha":
        return {"rajya_sabha": discovered["rajya_sabha"]}

    return discovered

def load_dataset(file_path: str | Path, parliament: str = "lok_sabha") -> dict:
    """
    Loads a single CSV/Excel dataset safely with encoding fallbacks and metadata recording.
    """
    p = Path(file_path)
    dataset_name = p.stem.lower()

    if not p.exists():
        return {
            "data": None,
            "metadata": {
                "parliament": parliament,
                "dataset_name": dataset_name,
                "source_file": str(p),
                "rows": 0,
                "columns": 0,
                "memory_mb": 0.0,
                "load_status": "failed",
                "error": f"File not found: {p}"
            }
        }

    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
    df = None
    last_err = None

    for enc in encodings:
        try:
            if p.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(p)
            else:
                df = pd.read_csv(
                    p,
                    encoding=enc,
                    skipinitialspace=True,
                    na_values=['', ' ', 'NA', 'N/A', 'NULL', 'null', 'None'],
                    keep_default_na=True,
                    low_memory=False
                )
            break
        except Exception as e:
            last_err = e
            continue

    if df is None:
        logger.error(f"Failed to load dataset {p.name}: {last_err}")
        return {
            "data": None,
            "metadata": {
                "parliament": parliament,
                "dataset_name": dataset_name,
                "source_file": str(p),
                "rows": 0,
                "columns": 0,
                "memory_mb": 0.0,
                "load_status": "failed",
                "error": str(last_err)
            }
        }

    # Clean whitespace around headers
    df.columns = [str(col).strip() for col in df.columns]
    mem_usage = round(float(df.memory_usage(deep=True).sum()) / (1024 * 1024), 2)

    metadata = {
        "parliament": parliament,
        "dataset_name": dataset_name,
        "source_file": str(p),
        "rows": len(df),
        "columns": len(df.columns),
        "memory_mb": mem_usage,
        "load_status": "success",
        "error": None
    }

    logger.info(f"Loaded [{parliament}] {p.name}: {len(df)} rows, {len(df.columns)} columns ({mem_usage} MB)")

    return {
        "data": df,
        "metadata": metadata
    }

class DataLoader:
    """
    NIRIKSHAK Dynamic Data Loader for Lok Sabha and Rajya Sabha MPLADS datasets.
    """

    def __init__(self, base_dir: str | Path = None):
        self.base_dir = Path(base_dir) if base_dir else DEFAULT_RAW_DIR

    def discover(self, parliament: str = "all") -> dict[str, list[Path]]:
        return discover_datasets(self.base_dir, parliament=parliament)

    def load_all(self, parliament: str = "all") -> dict[str, dict[str, dict]]:
        discovered = self.discover(parliament=parliament)
        results = {}

        for par, file_list in discovered.items():
            results[par] = {}
            for f in file_list:
                ds_res = load_dataset(f, parliament=par)
                ds_name = ds_res["metadata"]["dataset_name"]
                results[par][ds_name] = ds_res

        return results

def load_parliament_datasets(parliament: str = "lok_sabha", base_dir: str | Path = None) -> dict[str, dict]:
    loader = DataLoader(base_dir=base_dir)
    res = loader.load_all(parliament=parliament)
    return res.get(parliament, {})

def load_all_datasets(base_dir: str | Path = None) -> dict[str, dict[str, dict]]:
    loader = DataLoader(base_dir=base_dir)
    return loader.load_all(parliament="all")
