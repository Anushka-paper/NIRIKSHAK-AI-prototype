import os
import sys
import time
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "ml-service"))

from ingestion.data_loader import DataLoader
from profiling.profiler import profile_parliament
from preprocessing.standardization.standardizer import standardize_parliament

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PipelineOrchestrator")

class NirikshakPipeline:
    """
    NIRIKSHAK-AI Master Data Pipeline Orchestrator for Lok Sabha and Rajya Sabha Datasets.
    Orchestrates Discovery -> Loading -> Profiling -> Standardisation -> Validation -> Summary.
    """

    def __init__(self, raw_dir: str | Path = None, profiling_dir: str | Path = None, 
                 standardized_dir: str | Path = None, enable_er: bool = False, er_sample_limit: int = 1500,
                 enable_features: bool = False, fe_sample_limit: Optional[int] = None):
        self.raw_dir = Path(raw_dir) if raw_dir else (BASE_DIR / "data" / "raw")
        self.profiling_dir = Path(profiling_dir) if profiling_dir else (BASE_DIR / "data" / "profiling")
        self.standardized_dir = Path(standardized_dir) if standardized_dir else (BASE_DIR / "data" / "standardized")
        self.enable_er = enable_er
        self.er_sample_limit = er_sample_limit
        self.enable_features = enable_features
        self.fe_sample_limit = fe_sample_limit

    def run(self, parliament: str = "all") -> dict:
        """
        Executes complete pipeline for specified parliament scope ('lok_sabha', 'rajya_sabha', 'all').
        """
        start_time = time.time()
        logger.info(f"============================================================")
        logger.info(f"STARTING NIRIKSHAK PIPELINE FOR PARLIAMENT: {parliament.upper()}")
        logger.info(f"============================================================")

        parliaments_to_process = ["lok_sabha", "rajya_sabha"] if parliament == "all" else [parliament]

        loader = DataLoader(base_dir=self.raw_dir)
        discovered = loader.discover(parliament=parliament)

        pipeline_summary = {
            "execution_timestamp": datetime.now().isoformat(),
            "target_parliament_scope": parliament,
            "parliaments_processed": {},
            "total_processing_time_seconds": 0.0
        }

        for par in parliaments_to_process:
            par_start = time.time()
            logger.info(f"\n--- Processing [{par.upper()}] ---")

            file_list = discovered.get(par, [])
            if not file_list:
                logger.warning(f"No raw datasets discovered for [{par.upper()}]. Skipping.")
                pipeline_summary["parliaments_processed"][par] = {
                    "datasets_discovered": 0,
                    "status": "skipped_no_data"
                }
                continue

            # 1. Load Datasets
            logger.info(f"1. Loading {len(file_list)} datasets for [{par}]...")
            loaded_dict = loader.load_all(parliament=par).get(par, {})

            # 2. Profile Datasets
            logger.info(f"2. Running Dynamic Profiling for [{par}]...")
            profile_reports = {}
            try:
                profile_reports = profile_parliament(
                    parliament=par,
                    base_dir=self.raw_dir,
                    output_dir=self.profiling_dir,
                    verbose=False
                )
            except Exception as e:
                logger.error(f"Error during profiling for [{par}]: {e}")

            # 3. Standardize Datasets
            logger.info(f"3. Running Dynamic Standardisation & Validation for [{par}]...")
            std_reports = {}
            try:
                std_reports = standardize_parliament(
                    parliament=par,
                    base_dir=self.raw_dir,
                    output_dir=self.standardized_dir
                )
            except Exception as e:
                logger.error(f"Error during standardisation for [{par}]: {e}")

            # 4. Entity Resolution (Dynamic Work & Record Linking)
            er_report = {}
            if self.enable_er:
                logger.info(f"4. Running Dynamic Entity Resolution for [{par}]...")
                try:
                    from entity_resolution.resolver import resolve_parliament
                    er_report = resolve_parliament(
                        parliament=par,
                        sample_limit=self.er_sample_limit
                    )
                except Exception as e:
                    logger.error(f"Error during entity resolution for [{par}]: {e}")

            fe_report = None
            if self.enable_features:
                logger.info(f"5. Running Dynamic Feature Engineering for [{par}]...")
                try:
                    from features.feature_engineer import FeatureEngineer
                    fe_report = FeatureEngineer().engineer_parliament(
                        parliament=par,
                        sample_limit=self.fe_sample_limit
                    )
                except Exception as e:
                    logger.error(f"Error during feature engineering for [{par}]: {e}")

            par_time = round(time.time() - par_start, 2)
            pipeline_summary["parliaments_processed"][par] = {
                "datasets_discovered": len(file_list),
                "datasets_loaded_success": sum(1 for v in loaded_dict.values() if v["metadata"]["load_status"] == "success"),
                "datasets_loaded_failed": sum(1 for v in loaded_dict.values() if v["metadata"]["load_status"] == "failed"),
                "profiling_status": "success" if profile_reports else "failed",
                "standardization_status": "success" if std_reports else "failed",
                "entity_resolution_status": "success" if er_report else ("disabled" if not self.enable_er else "failed"),
                "feature_engineering_status": "success" if fe_report else ("disabled" if not self.enable_features else "failed"),
                "processing_time_seconds": par_time
            }

        total_time = round(time.time() - start_time, 2)
        pipeline_summary["total_processing_time_seconds"] = total_time

        # Save Pipeline Summary JSON
        summary_path = BASE_DIR / "data" / "pipeline_summary.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(pipeline_summary, f, indent=2)

        logger.info(f"\n============================================================")
        logger.info(f"PIPELINE EXECUTION COMPLETE IN {total_time}s")
        logger.info(f"Pipeline summary saved to: {summary_path}")
        logger.info(f"============================================================\n")

        return pipeline_summary

def main():
    parser = argparse.ArgumentParser(description="NIRIKSHAK-AI Master Data Pipeline")
    parser.add_argument("--parliament", "-p", default="all", choices=["lok_sabha", "rajya_sabha", "all"], help="Parliament scope")
    parser.add_argument("--raw-dir", help="Custom raw data directory")
    parser.add_argument("--profiling-dir", help="Custom profiling output directory")
    parser.add_argument("--standardized-dir", help="Custom standardized output directory")
    parser.add_argument("--resolve-entities", "-r", action="store_true", help="Execute entity resolution stage")
    parser.add_argument("--er-limit", type=int, default=1500, help="Candidate sample limit for entity resolution")
    parser.add_argument("--generate-features", "-f", action="store_true", help="Execute feature engineering stage")
    parser.add_argument("--fe-limit", type=int, default=None, help="Sample limit for feature engineering")

    args = parser.parse_args()

    pipeline = NirikshakPipeline(
        raw_dir=args.raw_dir,
        profiling_dir=args.profiling_dir,
        standardized_dir=args.standardized_dir,
        enable_er=args.resolve_entities,
        er_sample_limit=args.er_limit,
        enable_features=args.generate_features,
        fe_sample_limit=args.fe_limit
    )
    pipeline.run(parliament=args.parliament)

if __name__ == "__main__":
    main()

