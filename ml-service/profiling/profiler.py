import os
import sys
import argparse
import json
import re
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "ml-service"))

from profiling.type_detector import detect_column_type
from profiling.quality_checks import run_quality_checks
from profiling.identifier_checks import run_identifier_checks
from profiling.amount_checks import run_amount_checks
from profiling.date_checks import run_date_checks
from profiling.categorical_checks import run_categorical_checks
from profiling.text_checks import run_text_checks
from profiling.relationship_checks import run_relationship_checks
from profiling.mplads_checks import run_mplads_profiling
from profiling.report_generator import (
    build_json_report,
    print_console_report,
    export_parliament_profiling_artifacts
)
from ingestion.data_loader import DataLoader

SUMMARY_ROW_PATTERN = r'(?i)^(grand\s+total|total|summary)[\:\s]*$'

def load_dataset_from_file(file_path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    """
    Robust CSV Loader. Handles encodings (UTF-8, UTF-8-sig, Latin-1), header whitespace,
    missing value strings, and summary row detection.
    Returns (record_df, summary_df, summary_row_count).
    """
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset file not found at: {file_path}")

    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
    raw_df = None

    for enc in encodings:
        try:
            raw_df = pd.read_csv(
                file_path,
                encoding=enc,
                skipinitialspace=True,
                na_values=['', ' ', 'NA', 'N/A', 'NULL', 'null', 'None'],
                keep_default_na=True,
                low_memory=False
            )
            break
        except Exception:
            continue

    if raw_df is None:
        raise ValueError(f"Could not parse CSV file: {file_path}")

    raw_df.columns = [str(col).strip() for col in raw_df.columns]

    if raw_df.empty:
        return raw_df, pd.DataFrame(), 0

    summary_mask = pd.Series(False, index=raw_df.index)
    for col in raw_df.columns:
        if raw_df[col].dtype == object or pd.api.types.is_string_dtype(raw_df[col]):
            matches = raw_df[col].astype(str).str.strip().str.match(SUMMARY_ROW_PATTERN, na=False)
            summary_mask = summary_mask | matches

    summary_df = raw_df[summary_mask].copy()
    record_df = raw_df[~summary_mask].copy()
    summary_count = int(summary_mask.sum())

    return record_df, summary_df, summary_count

class DataProfiler:
    """
    NIRIKSHAK Dynamic Data Profiler for Lok Sabha and Rajya Sabha Datasets.
    """

    def __init__(self, file_path: str | Path = None, df: pd.DataFrame = None, parliament: str = "lok_sabha"):
        self.file_path = Path(file_path) if file_path else None
        self.dataset_name = self.file_path.name if self.file_path else "in_memory_dataset"
        self.df = df
        self.parliament = parliament

    def profile(self, verbose: bool = True) -> dict:
        """Runs complete dynamic profiling workflow on dataset."""
        if self.df is not None:
            raw_df = self.df
            summary_mask = pd.Series(False, index=raw_df.index)
            for col in raw_df.columns:
                if raw_df[col].dtype == object or pd.api.types.is_string_dtype(raw_df[col]):
                    matches = raw_df[col].astype(str).str.strip().str.match(SUMMARY_ROW_PATTERN, na=False)
                    summary_mask = summary_mask | matches
            summary_df = raw_df[summary_mask].copy()
            record_df = raw_df[~summary_mask].copy()
            summary_row_count = int(summary_mask.sum())
        else:
            record_df, summary_df, summary_row_count = load_dataset_from_file(self.file_path)

        total_rows = len(record_df) + summary_row_count
        record_rows = len(record_df)
        total_cols = len(record_df.columns)

        if record_rows == 0:
            print(f"WARNING: Dataset {self.dataset_name} is empty.")

        # 1. Dynamic Column Type Detection
        schema = []
        col_type_buckets = {
            "identifier": [], "currency": [], "numeric": [],
            "date": [], "categorical": [], "text": [], "boolean": []
        }

        for col in record_df.columns:
            dt_type = detect_column_type(record_df[col], col)
            schema.append({
                "column_name": col,
                "original_dtype": str(record_df[col].dtype),
                "detected_type": dt_type
            })
            if dt_type in col_type_buckets:
                col_type_buckets[dt_type].append(col)
            else:
                col_type_buckets["categorical"].append(col)

        # 2. Run Module Profiling Checks
        quality_res = run_quality_checks(record_df)
        identifier_res = run_identifier_checks(record_df, col_type_buckets["identifier"])
        amount_res = run_amount_checks(record_df, col_type_buckets["numeric"], col_type_buckets["currency"])
        date_res = run_date_checks(record_df, col_type_buckets["date"])
        categorical_res = run_categorical_checks(record_df, col_type_buckets["categorical"] + col_type_buckets["boolean"])
        text_res = run_text_checks(record_df, col_type_buckets["text"])
        relationship_res = run_relationship_checks(record_df)
        mplads_res = run_mplads_profiling(record_df)

        # 3. Generate Master Report
        report = build_json_report(
            dataset_name=self.dataset_name,
            parliament=self.parliament,
            total_rows=total_rows,
            record_rows=record_rows,
            summary_rows=summary_row_count,
            total_cols=total_cols,
            schema=schema,
            quality_res=quality_res,
            identifier_res=identifier_res,
            amount_res=amount_res,
            date_res=date_res,
            categorical_res=categorical_res,
            text_res=text_res,
            relationship_res=relationship_res,
            mplads_res=mplads_res
        )

        if verbose:
            print_console_report(report)

        return report

def profile_dataset(file_path: str | Path, parliament: str = "lok_sabha", verbose: bool = True) -> dict:
    """Profiles a single CSV dataset."""
    profiler = DataProfiler(file_path=file_path, parliament=parliament)
    return profiler.profile(verbose=verbose)

def profile_parliament(parliament: str = "lok_sabha", base_dir: str | Path = None, output_dir: str | Path = None, verbose: bool = True) -> dict:
    """Profiles all discovered datasets for a single parliament and exports 15 profiling artifacts."""
    loader = DataLoader(base_dir=base_dir)
    ds_dict = loader.load_all(parliament=parliament).get(parliament, {})

    if not ds_dict:
        print(f"No datasets discovered for parliament: {parliament}")
        return {}

    print(f"\nProfiling {len(ds_dict)} datasets for [{parliament.upper()}]...")
    parliament_reports = {}

    for ds_name, item in ds_dict.items():
        if item["metadata"]["load_status"] == "failed":
            print(f"ERROR: Dataset {ds_name} failed to load: {item['metadata']['error']}")
            parliament_reports[ds_name] = {"error": item["metadata"]["error"]}
            continue

        df = item["data"]
        profiler = DataProfiler(file_path=item["metadata"]["source_file"], df=df, parliament=parliament)
        rep = profiler.profile(verbose=verbose)
        parliament_reports[ds_name] = rep

    out_base = Path(output_dir) if output_dir else (BASE_DIR / "data" / "profiling")
    export_parliament_profiling_artifacts(parliament, parliament_reports, out_base)

    print(f"\nExported 15 profiling reports for [{parliament.upper()}] to: {out_base / parliament}")
    return parliament_reports

def profile_directory(dir_path: str | Path, parliament: str = "all", verbose: bool = True, output_dir: str | Path = None) -> dict:
    """Profiles all datasets in a directory or parliament scope."""
    out_base = Path(output_dir) if output_dir else (BASE_DIR / "data" / "profiling")

    if parliament == "all":
        ls_reps = profile_parliament(parliament="lok_sabha", base_dir=dir_path, output_dir=out_base, verbose=verbose)
        rs_reps = profile_parliament(parliament="rajya_sabha", base_dir=dir_path, output_dir=out_base, verbose=verbose)
        return {"lok_sabha": ls_reps, "rajya_sabha": rs_reps}
    else:
        return profile_parliament(parliament=parliament, base_dir=dir_path, output_dir=out_base, verbose=verbose)

def main():
    parser = argparse.ArgumentParser(description="NIRIKSHAK Dynamic Data Profiler")
    parser.add_argument("path", nargs="?", help="Path to single CSV file to profile")
    parser.add_argument("--parliament", "-p", default="all", choices=["lok_sabha", "rajya_sabha", "all"], help="Parliament scope")
    parser.add_argument("--directory", "-d", help="Path to directory containing datasets")
    parser.add_argument("--output", "-o", help="Output directory for profiling artifacts")

    args = parser.parse_args()

    if args.path:
        report = profile_dataset(args.path, parliament=args.parliament, verbose=True)
        if args.output:
            out_p = Path(args.output)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to: {args.output}")
    else:
        profile_directory(args.directory or (BASE_DIR / "data" / "raw"), parliament=args.parliament, verbose=True, output_dir=args.output)

if __name__ == "__main__":
    main()