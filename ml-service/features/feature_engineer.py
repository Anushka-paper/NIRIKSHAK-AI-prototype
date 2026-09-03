"""
Master Feature Engineering Pipeline and CLI for NIRIKSHAK-AI.
Transforms integrated MPLADS data into leakage-safe feature datasets.
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

# Ensure module path resolution
CURRENT_DIR = Path(__file__).resolve().parent
SERVICE_DIR = CURRENT_DIR.parent
BASE_DIR = SERVICE_DIR.parent
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

from integration.work_master import build_unified_work_master
from features.entity_features import compute_entity_features
from features.financial_features import compute_financial_features
from features.temporal_features import compute_temporal_and_lifecycle_features
from features.text_features import compute_text_features
from features.historical_features import compute_leakage_safe_historical_features
from features.statistical_features import compute_statistical_features
from features.aggregation_features import compute_group_aggregations
from features.leakage_checker import check_feature_leakage
from features.quality_reporter import generate_feature_dictionary, audit_feature_quality

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("NIRIKSHAK-FEATURE-ENGINEER")

class FeatureEngineer:
    """
    Orchestrates the dynamic feature engineering pipeline across all 26 feature groups.
    """
    def __init__(self, output_base_dir: Optional[Path] = None):
        self.output_base = output_base_dir or (BASE_DIR / "data" / "features")

    def engineer_parliament(self, parliament: str = "lok_sabha", sample_limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Executes end-to-end feature engineering for a specific parliament.
        """
        start_time = time.time()
        logger.info(f"\n============================================================")
        logger.info(f"STARTING FEATURE ENGINEERING FOR: {parliament.upper()}")
        logger.info(f"============================================================")

        out_dir = self.output_base / parliament
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Build Unified Work Master & Transaction Master
        logger.info(f"1. Building Unified Work Master and Transaction Tables for [{parliament}]...")
        work_master_df, transaction_df = build_unified_work_master(parliament=parliament)

        if work_master_df.empty:
            logger.warning(f"No records available to engineer features for [{parliament}].")
            return {"status": "empty", "parliament": parliament}

        if sample_limit and len(work_master_df) > sample_limit:
            logger.info(f"Applying sample limit of {sample_limit} rows for performance...")
            work_master_df = work_master_df.iloc[:sample_limit].copy()

        # 2. Sequential Feature Generation
        logger.info(f"2. Generating Entity, Provenance & Lineage Features...")
        df = compute_entity_features(work_master_df)

        logger.info(f"3. Generating Financial Differences, Ratios & Gap Features...")
        df = compute_financial_features(df)

        logger.info(f"4. Generating Temporal, Lifecycle Duration & Chronology Features...")
        df = compute_temporal_and_lifecycle_features(df)

        logger.info(f"5. Generating Text Complexity & Syntactic Features...")
        df = compute_text_features(df)

        logger.info(f"6. Generating Leakage-Safe Time-Aware Historical Features...")
        df = compute_leakage_safe_historical_features(df)

        logger.info(f"7. Generating Statistical, Distribution & Outlier Signals...")
        df = compute_statistical_features(df)

        # 3. Dimension Aggregations (MP, Constituency, State, Vendor)
        logger.info(f"8. Generating MP, Constituency, State, and Vendor Dimension Tables...")
        mp_df, const_df, state_df, vendor_df = compute_group_aggregations(df)

        # 4. Leakage & Quality Auditing
        logger.info(f"9. Running Feature Leakage Audit and Quality Validation...")
        leakage_df = check_feature_leakage(list(df.columns))
        dictionary_df = generate_feature_dictionary(df)
        quality_df = audit_feature_quality(df)

        # 5. Export All Artifacts
        logger.info(f"10. Exporting Feature Tables and Metadata Reports...")
        
        # Master Work Features
        work_csv = out_dir / "work_features.csv"
        df.to_csv(work_csv, index=False)
        logger.info(f"Saved Work Features: {work_csv} ({len(df)} rows, {len(df.columns)} features)")

        # Transaction Features
        tx_csv = out_dir / "transaction_features.csv"
        if not transaction_df.empty:
            transaction_df.to_csv(tx_csv, index=False)
            logger.info(f"Saved Transaction Features: {tx_csv} ({len(transaction_df)} transactions)")

        # Dimension Tables
        mp_csv = out_dir / "mp_features.csv"
        mp_df.to_csv(mp_csv, index=False)
        logger.info(f"Saved MP Features: {mp_csv} ({len(mp_df)} MPs)")

        const_csv = out_dir / "constituency_features.csv"
        const_df.to_csv(const_csv, index=False)
        logger.info(f"Saved Constituency Features: {const_csv} ({len(const_df)} constituencies)")

        state_csv = out_dir / "state_features.csv"
        state_df.to_csv(state_csv, index=False)
        logger.info(f"Saved State Features: {state_csv} ({len(state_df)} states)")

        vendor_csv = out_dir / "vendor_features.csv"
        vendor_df.to_csv(vendor_csv, index=False)
        logger.info(f"Saved Vendor Features: {vendor_csv} ({len(vendor_df)} vendors)")

        # Reports
        dict_csv = out_dir / "feature_dictionary.csv"
        dictionary_df.to_csv(dict_csv, index=False)

        leakage_csv = out_dir / "feature_leakage_report.csv"
        leakage_df.to_csv(leakage_csv, index=False)

        quality_csv = out_dir / "feature_quality_report.csv"
        quality_df.to_csv(quality_csv, index=False)

        elapsed = round(time.time() - start_time, 2)
        summary = {
            "parliament": parliament,
            "total_works_processed": len(df),
            "total_features_generated": len(df.columns),
            "total_transactions": len(transaction_df),
            "total_mps": len(mp_df),
            "total_constituencies": len(const_df),
            "total_states": len(state_df),
            "total_vendors": len(vendor_df),
            "elapsed_seconds": elapsed,
            "feature_schema_version": "v1.0",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        summary_json = out_dir / "feature_generation_report.json"
        with open(summary_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Feature engineering for [{parliament}] completed in {elapsed}s.")
        logger.info(f"============================================================\n")
        return summary

def run_feature_engineering(parliament: str = "all", sample_limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Runs feature engineering across requested parliaments.
    """
    engineer = FeatureEngineer()
    parliaments = ["lok_sabha", "rajya_sabha"] if parliament == "all" else [parliament]
    results = {}
    for p in parliaments:
        results[p] = engineer.engineer_parliament(parliament=p, sample_limit=sample_limit)
    return results

def main():
    parser = argparse.ArgumentParser(description="NIRIKSHAK-AI Dynamic Feature Engineering Engine")
    parser.add_argument("--parliament", "-p", default="all", choices=["lok_sabha", "rajya_sabha", "all"])
    parser.add_argument("--limit", type=int, default=None, help="Optional row limit for test runs")
    args = parser.parse_args()

    run_feature_engineering(parliament=args.parliament, sample_limit=args.limit)

if __name__ == "__main__":
    main()

