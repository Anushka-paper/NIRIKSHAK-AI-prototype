"""
NIRIKSHAK-AI Master Schema-Aware Pipeline Orchestrator (Stages 0 to 6)
Executes:
  Stage 0 — RAW INGESTION (ingests all 6 datasets without merging, partitions by house)
  Stage 1 — SCHEMA VALIDATION & QUARANTINE (enforces grain, isolates ambiguous fields)
  Stage 2 — ENTITY RESOLUTION & CLEANING (MPs, Constituencies, IDAs, Vendors, clean currency, category taxonomy)
  Stage 3 — LIFECYCLE INTEGRATION (anchor join, synthetic txn_id, chronology validation, exports 11 Canonical Tables)
  Stage 4 — BASE FEATURE ENGINEERING (cost deviation, lifecycle durations, overpayment, budget breach, feature store)
  Stage 5 — MODEL-SPECIFIC ADAPTERS (decoupled subsets for dedup, cost anomaly, delay, forecasting, graph, calamity)
  Stage 6 — SUMMARY & AUDIT LOGGING
"""

import os
import sys
import time
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import pandas as pd

# Path resolution
BASE_DIR = Path(__file__).resolve().parent.parent
SERVICE_DIR = BASE_DIR / "ml-service"
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(SERVICE_DIR))

from ingestion.schema_loader import ingest_raw_datasets
from preprocessing.schema_validator import validate_and_quarantine
from preprocessing.entity_cleaner import clean_dataset
from integration.lifecycle_integrator import integrate_lifecycle
from features.base_features import compute_base_features
from models.model_adapters import ModelAdapters

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MasterPipelineOrchestrator")

def run_master_schema_pipeline(parliament: str = "all") -> Dict[str, Any]:
    start_time = time.time()
    logger.info("=" * 65)
    logger.info(f"STARTING SCHEMA-AWARE 7-STAGE PIPELINE FOR: {parliament.upper()}")
    logger.info("=" * 65)

    parliaments = ["lok_sabha", "rajya_sabha"] if parliament == "all" else [parliament]
    pipeline_report = {
        "execution_timestamp": datetime.now().isoformat(),
        "parliament_scope": parliament,
        "stages": [
            "Stage 0: Raw Ingestion",
            "Stage 1: Schema Validation & Quarantine",
            "Stage 2: Entity Resolution & Cleaning",
            "Stage 3: Lifecycle Integration (11 Canonical Tables)",
            "Stage 4: Base Feature Engineering (Feature Store)",
            "Stage 5: Model Adapters Preparation",
            "Stage 6: Scoring & Audit Reporting"
        ],
        "parliaments_processed": {},
        "total_duration_seconds": 0.0
    }

    for house in parliaments:
        h_start = time.time()
        logger.info(f"\n>>>> Executing Stages 0 to 6 for [{house.upper()}] <<<<")

        # -------------------------------------------------------------------------
        # Stage 0: RAW INGESTION
        # -------------------------------------------------------------------------
        logger.info(f"[STAGE 0] Ingesting all 6 raw datasets separately for {house}...")
        raw_datasets = ingest_raw_datasets(parliament=house)
        if not raw_datasets:
            logger.warning(f"No raw datasets discovered for {house}. Skipping.")
            continue

        # -------------------------------------------------------------------------
        # Stage 1: SCHEMA VALIDATION & QUARANTINE
        # -------------------------------------------------------------------------
        logger.info(f"[STAGE 1] Running schema validation and quarantine for {house}...")
        validated_datasets = {}
        stage1_report = {}
        for ds_type, meta in raw_datasets.items():
            valid_df, quarantined_df, rep = validate_and_quarantine(
                df=meta["df"],
                dataset_type=ds_type,
                parliament=house
            )
            validated_datasets[ds_type] = valid_df
            stage1_report[ds_type] = rep

        # -------------------------------------------------------------------------
        # Stage 2: ENTITY RESOLUTION & CLEANING
        # -------------------------------------------------------------------------
        logger.info(f"[STAGE 2] Running entity resolution, vocabulary mapping & currency cleaning for {house}...")
        cleaned_datasets = {}
        for ds_type, df in validated_datasets.items():
            cleaned_datasets[ds_type] = clean_dataset(df=df, dataset_type=ds_type, parliament=house)

        # -------------------------------------------------------------------------
        # Stage 3: LIFECYCLE INTEGRATION (11 Canonical Tables)
        # -------------------------------------------------------------------------
        logger.info(f"[STAGE 3] Integrating lifecycle, validating chronology, and emitting 11 Canonical Tables for {house}...")
        canonical_tables = integrate_lifecycle(
            cleaned_datasets=cleaned_datasets,
            parliament=house
        )

        # -------------------------------------------------------------------------
        # Stage 4: BASE FEATURE ENGINEERING
        # -------------------------------------------------------------------------
        logger.info(f"[STAGE 4] Engineering base features and updating Canonical Feature Store for {house}...")
        feature_store = compute_base_features(
            canonical_tables=canonical_tables,
            parliament=house
        )

        # -------------------------------------------------------------------------
        # Stage 5: MODEL-SPECIFIC ADAPTERS
        # -------------------------------------------------------------------------
        logger.info(f"[STAGE 5] Generating decoupled model datasets for {house}...")
        dedup_data = ModelAdapters.get_dedup_dataset(canonical_tables.get("Works", pd.DataFrame()))
        cost_data = ModelAdapters.get_cost_anomaly_dataset(feature_store)
        delay_data = ModelAdapters.get_delay_prediction_dataset(feature_store)
        forecast_data = ModelAdapters.get_trend_forecast_dataset(canonical_tables.get("Expenditure", pd.DataFrame()))
        vendor_graph = ModelAdapters.get_vendor_graph_edgelist(canonical_tables.get("Expenditure", pd.DataFrame()))
        calamity_data = ModelAdapters.get_calamity_anomaly_dataset(canonical_tables.get("Calamity_Consent", pd.DataFrame()))

        h_duration = round(time.time() - h_start, 2)
        pipeline_report["parliaments_processed"][house] = {
            "datasets_ingested": len(raw_datasets),
            "canonical_tables_generated": len([k for k in canonical_tables.keys() if k != "Lifecycle_Merged"]),
            "canonical_works_count": len(canonical_tables.get("Works", [])),
            "canonical_expenditures_count": len(canonical_tables.get("Expenditure", [])),
            "feature_store_features": len(feature_store.columns) if not feature_store.empty else 0,
            "validation_report": stage1_report,
            "duration_seconds": h_duration
        }
        logger.info(f">>>> Completed [{house.upper()}] in {h_duration}s <<<<\n")

    total_time = round(time.time() - start_time, 2)
    pipeline_report["total_duration_seconds"] = total_time

    # Save summary
    out_summary = BASE_DIR / "data" / "pipeline_summary.json"
    with open(out_summary, "w", encoding="utf-8") as fp:
        json.dump(pipeline_report, fp, indent=2)

    logger.info("=" * 65)
    logger.info(f"SCHEMA-AWARE PIPELINE COMPLETED IN {total_time}s")
    logger.info(f"Summary persisted to: {out_summary}")
    logger.info("=" * 65)
    return pipeline_report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Schema-Aware Master Data Pipeline")
    parser.add_argument("--parliament", "-p", default="all", choices=["lok_sabha", "rajya_sabha", "all"])
    args = parser.parse_args()
    run_master_schema_pipeline(parliament=args.parliament)
