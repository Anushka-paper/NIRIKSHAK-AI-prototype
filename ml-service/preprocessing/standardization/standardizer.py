import os
import sys
import argparse
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "ml-service"))

from preprocessing.standardization.detectors import normalize_column_name, detect_column_rule_type
from preprocessing.standardization.column_mappings import COLUMN_MAPPINGS
from preprocessing.standardization.validator import validate_standardized_dataframe
from preprocessing.standardization.utils import (
    is_missing_value,
    clean_text,
    standardize_state_value,
    standardize_currency_value,
    standardize_date_iso,
    standardize_person_name,
    standardize_identifier_string,
    standardize_boolean_value,
    standardize_status_value,
    standardize_category_vocabulary
)
from ingestion.data_loader import DataLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DataStandardizer")

class DataStandardizer:
    """
    NIRIKSHAK Dynamic Data Standardisation Engine.
    Transforms raw heterogeneous datasets for Lok Sabha and Rajya Sabha into canonical representations.
    """

    def __init__(self, parliament: str = "lok_sabha", config: dict = None):
        self.parliament = parliament
        self.config = config or {}
        self.parliament_mappings = COLUMN_MAPPINGS.get(parliament, {})

    def standardize(self, df: pd.DataFrame, profiling_report: dict = None) -> dict:
        """
        Executes dynamic standardization pipeline on DataFrame.
        Returns dict containing standardized 'data' (DataFrame) and 'report' (dict).
        """
        if df.empty:
            return {
                "data": df.copy(),
                "report": {
                    "parliament": self.parliament,
                    "rows_processed": 0,
                    "columns_processed": 0,
                    "transformations": {},
                    "invalid_values": [],
                    "warnings": ["Input dataframe is empty"]
                }
            }

        df_orig = df.copy()
        record_rows = len(df_orig)

        # 1. Normalize Column Names using parliament-specific mappings or dynamic normalizer
        original_cols = list(df_orig.columns)
        col_renames = {}
        for col in original_cols:
            col_renames[col] = normalize_column_name(col)

        df_std = df_orig.rename(columns=col_renames)
        new_cols = list(df_std.columns)

        transformations = {}
        invalid_values = []

        # 2. Process Each Column Dynamically
        for orig_col in original_cols:
            norm_col = col_renames[orig_col]
            rule_type = self.config.get(norm_col, {}).get("type") or detect_column_rule_type(orig_col, df_orig[orig_col], profiling_report)

            raw_series = df_orig[orig_col]
            std_series = []
            values_changed_count = 0
            invalid_count = 0

            for val in raw_series:
                new_val = val
                changed = False

                if rule_type == 'state':
                    new_val, changed = standardize_state_value(val)
                elif rule_type == 'currency':
                    new_val, changed = standardize_currency_value(val)
                    if val is not None and not is_missing_value(val) and new_val is None:
                        invalid_count += 1
                        invalid_values.append({"column": norm_col, "raw_value": str(val), "reason": "Failed currency parse"})
                elif rule_type == 'date':
                    new_val, changed = standardize_date_iso(val)
                    if val is not None and not is_missing_value(val) and new_val is None:
                        invalid_count += 1
                        invalid_values.append({"column": norm_col, "raw_value": str(val), "reason": "Failed ISO date parse"})
                elif rule_type == 'person_name':
                    new_val, changed = standardize_person_name(val)
                elif rule_type == 'identifier':
                    new_val, changed = standardize_identifier_string(val)
                elif rule_type == 'boolean':
                    new_val, changed = standardize_boolean_value(val)
                elif rule_type == 'status':
                    new_val, changed = standardize_status_value(val)
                elif rule_type == 'category':
                    new_val, changed = standardize_category_vocabulary(val)
                else: # text / fallback
                    new_val = clean_text(val)
                    changed = (str(val) != str(new_val)) if (val is not None and new_val is not None) else False

                if changed:
                    values_changed_count += 1
                std_series.append(new_val)

            df_std[norm_col] = std_series
            transformations[norm_col] = {
                "original_column": orig_col,
                "rule_applied": rule_type,
                "values_changed": values_changed_count,
                "values_unchanged": record_rows - values_changed_count,
                "invalid_values_count": invalid_count
            }

        # 3. Post-Standardisation Validation
        validation_res = validate_standardized_dataframe(df_std)

        report = {
            "parliament": self.parliament,
            "rows_processed": record_rows,
            "columns_processed": len(new_cols),
            "transformations": transformations,
            "invalid_values": invalid_values[:50],
            "validation": validation_res,
            "warnings": validation_res["validation_warnings"],
            "errors": validation_res["validation_errors"]
        }

        return {
            "data": df_std,
            "report": report
        }

def standardize_file(input_file: str | Path, output_file: str | Path = None, parliament: str = "lok_sabha", config: dict = None) -> dict:
    """Standardises a single CSV or XLSX file and optionally saves standardized dataset and report."""
    in_p = Path(input_file)
    if not in_p.exists():
        raise FileNotFoundError(f"Input dataset file not found: {input_file}")

    logger.info(f"Loading [{parliament.upper()}] dataset: {in_p.name}")

    if in_p.suffix.lower() in ['.xlsx', '.xls']:
        df = pd.read_excel(in_p)
    else:
        encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
        df = None
        for enc in encodings:
            try:
                df = pd.read_csv(in_p, encoding=enc, low_memory=False)
                break
            except Exception:
                continue
        if df is None:
            raise ValueError(f"Could not parse file: {input_file}")

    standardizer = DataStandardizer(parliament=parliament, config=config)
    result = standardizer.standardize(df)

    if output_file:
        out_p = Path(output_file)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        if out_p.suffix.lower() in ['.xlsx', '.xls']:
            result["data"].to_excel(out_p, index=False)
        else:
            result["data"].to_csv(out_p, index=False)

        report_p = out_p.parent / f"{out_p.stem}_report.json"
        with open(report_p, "w", encoding="utf-8") as f:
            json.dump(result["report"], f, indent=2)

        logger.info(f"Saved standardized dataset: {out_p}")
        logger.info(f"Saved report: {report_p}")

    return result

def standardize_dataset(input_file: str | Path, output_file: str | Path = None, parliament: str = "lok_sabha", config: dict = None) -> dict:
    """Alias for standardize_file."""
    return standardize_file(input_file, output_file, parliament=parliament, config=config)

def standardize_parliament(parliament: str = "lok_sabha", base_dir: str | Path = None, output_dir: str | Path = None, config: dict = None) -> dict:
    """
    Standardises all discovered datasets for a single parliament and saves to data/standardized/<parliament>/
    """
    loader = DataLoader(base_dir=base_dir)
    ds_dict = loader.load_all(parliament=parliament).get(parliament, {})

    out_base = Path(output_dir) if output_dir else (BASE_DIR / "data" / "standardized")
    par_out_dir = out_base / parliament
    par_out_dir.mkdir(parents=True, exist_ok=True)

    if not ds_dict:
        logger.warning(f"No datasets discovered for parliament: {parliament}")
        return {}

    logger.info(f"Standardizing {len(ds_dict)} datasets for [{parliament.upper()}]...")
    results = {}

    for ds_name, item in ds_dict.items():
        if item["metadata"]["load_status"] == "failed":
            logger.error(f"Dataset {ds_name} failed to load: {item['metadata']['error']}")
            results[ds_name] = {"error": item["metadata"]["error"]}
            continue

        src_path = Path(item["metadata"]["source_file"])
        out_file = par_out_dir / f"{src_path.stem}_standardized{src_path.suffix}"
        res = standardize_file(src_path, out_file, parliament=parliament, config=config)
        results[ds_name] = res["report"]

    return results

def standardize_directory(input_dir: str | Path, output_dir: str | Path, parliament: str = "all", config: dict = None) -> dict:
    """Standardises datasets across parliament scope."""
    out_base = Path(output_dir) if output_dir else (BASE_DIR / "data" / "standardized")

    if parliament == "all":
        ls_res = standardize_parliament(parliament="lok_sabha", base_dir=input_dir, output_dir=out_base, config=config)
        rs_res = standardize_parliament(parliament="rajya_sabha", base_dir=input_dir, output_dir=out_base, config=config)
        return {"lok_sabha": ls_res, "rajya_sabha": rs_res}
    else:
        return standardize_parliament(parliament=parliament, base_dir=input_dir, output_dir=out_base, config=config)

def main():
    parser = argparse.ArgumentParser(description="NIRIKSHAK Dynamic Data Standardisation Engine")
    parser.add_argument("path", nargs="?", help="Path to single CSV/XLSX file to standardize")
    parser.add_argument("--parliament", "-p", default="all", choices=["lok_sabha", "rajya_sabha", "all"], help="Parliament scope")
    parser.add_argument("--directory", "-d", help="Path to raw datasets directory")
    parser.add_argument("--output", "-o", help="Path to output directory")

    args = parser.parse_args()

    if args.path:
        out_f = args.output if args.output else str(Path(args.path).parent / f"{Path(args.path).stem}_standardized.csv")
        res = standardize_file(args.path, out_f, parliament=args.parliament)
        print(f"\nStandardization complete. Saved to: {out_f}")
    else:
        out_d = args.output if args.output else str(BASE_DIR / "data" / "standardized")
        standardize_directory(args.directory or (BASE_DIR / "data" / "raw"), out_d, parliament=args.parliament)
        print(f"\nBatch standardization complete. Saved to: {out_d}")

if __name__ == "__main__":
    main()
