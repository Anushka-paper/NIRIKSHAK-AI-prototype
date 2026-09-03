"""
Dynamic Entity Resolution Master Resolver for NIRIKSHAK-AI.
Orchestrates entity discovery, candidate blocking, exact and fuzzy matching,
multi-field scoring, confidence classification, and provenance preservation.
"""

import os
import sys
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "ml-service"))

from entity_resolution.column_mapper import ColumnMapper
from entity_resolution.candidate_generator import CandidateGenerator
from entity_resolution.exact_matcher import ExactMatcher
from entity_resolution.fuzzy_matcher import FuzzyMatcher
from entity_resolution.scoring import ScoringEngine
from entity_resolution.confidence import ConfidenceClassifier
from entity_resolution.provenance import ProvenanceManager
from entity_resolution.review_queue import ReviewQueueManager
from entity_resolution.report_generator import ReportGenerator
from entity_resolution.config import SPECIAL_DATASET_TYPES

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("EntityResolver")

class EntityResolver:
    """
    Master Entity Resolver for MPLADS Works across Parliaments.
    """

    def __init__(self, parliament: str = "lok_sabha", standardized_dir: str | Path = None,
                 output_dir: str | Path = None):
        self.parliament = parliament
        self.standardized_dir = Path(standardized_dir) if standardized_dir else (BASE_DIR / "data" / "standardized" / parliament)
        self.output_dir = Path(output_dir) if output_dir else (BASE_DIR / "data" / "entity_resolution" / parliament)

        self.column_mapper = ColumnMapper()
        self.candidate_generator = CandidateGenerator()
        self.exact_matcher = ExactMatcher()
        self.fuzzy_matcher = FuzzyMatcher()
        self.scoring_engine = ScoringEngine()
        self.confidence_classifier = ConfidenceClassifier()
        self.provenance_manager = ProvenanceManager()
        self.review_queue = ReviewQueueManager()
        self.report_generator = ReportGenerator()

    def discover_datasets(self) -> dict[str, Path]:
        """
        Discovers all available standardized datasets for the parliament.
        Excludes special aggregate streams (e.g. allocation, calamity).
        """
        if not self.standardized_dir.exists():
            logger.warning(f"Standardized directory not found: {self.standardized_dir}")
            return {}

        discovered = {}
        for f in self.standardized_dir.glob("*_standardized.csv"):
            stem = f.stem.replace("_standardized", "").lower()
            # Check special dataset exclusion
            is_special = False
            for sp_key in SPECIAL_DATASET_TYPES:
                if sp_key in stem:
                    logger.info(f"Skipping special stream from direct work ER: {f.name} ({SPECIAL_DATASET_TYPES[sp_key]})")
                    is_special = True
                    break
            if not is_special:
                discovered[stem] = f

        return discovered

    def resolve_dataset_pair(self, ds_name_a: str, path_a: Path, 
                             ds_name_b: str, path_b: Path,
                             sample_limit: int = 1500) -> dict:
        """
        Performs entity resolution between two standardized datasets.
        """
        logger.info(f"Resolving entities: [{ds_name_a}] <---> [{ds_name_b}]")
        df_a = pd.read_csv(path_a, low_memory=False)
        df_b = pd.read_csv(path_b, low_memory=False)

        # Cap for interactive / prototype performance if extremely large
        if sample_limit and len(df_a) > sample_limit:
            df_a = df_a.head(sample_limit)
        if sample_limit and len(df_b) > sample_limit:
            df_b = df_b.head(sample_limit)

        map_a = self.column_mapper.detect_semantic_columns(df_a)
        map_b = self.column_mapper.detect_semantic_columns(df_b)

        logger.info(f"  [{ds_name_a}] mapped fields: {list(map_a.keys())}")
        logger.info(f"  [{ds_name_b}] mapped fields: {list(map_b.keys())}")

        # Ensure minimal required fields (state or mp or work_id)
        if not any(k in map_a for k in ["work_id", "state", "mp_name"]) or not any(k in map_b for k in ["work_id", "state", "mp_name"]):
            logger.warning(f"Insufficient fields for ER between {ds_name_a} and {ds_name_b}")
            return {
                "dataset_pair": f"{ds_name_a} -> {ds_name_b}",
                "status": "insufficient_fields",
                "candidate_pairs": 0,
                "high_confidence_matches": 0,
                "review_count": 0,
                "unresolved_count": len(df_a)
            }

        candidates = self.candidate_generator.generate_candidate_blocks(df_a, df_b, map_a, map_b)
        logger.info(f"  Generated {len(candidates)} candidate pairs to evaluate")

        matched_records = []
        matched_a_indices = set()
        matched_b_indices = set()

        # Step 1: Exact Matching
        remaining_candidates = []
        for idx_a, idx_b, strategy in candidates:
            row_a = df_a.iloc[idx_a]
            row_b = df_b.iloc[idx_b]

            exact_res = self.exact_matcher.match(row_a, row_b, map_a, map_b)
            if exact_res and exact_res.get("is_match"):
                off_wid = exact_res.get("official_work_id")
                can_id = self.provenance_manager.get_or_create_canonical_id(off_wid, ds_name_a, idx_a)
                self.provenance_manager.link_entities(can_id, off_wid, ds_name_b, idx_b)

                matched_records.append({
                    "canonical_work_id": can_id,
                    "source_parliament": self.parliament,
                    "source_dataset": ds_name_a,
                    "source_row_id": idx_a,
                    "matched_dataset": ds_name_b,
                    "matched_row_id": idx_b,
                    "official_work_id": off_wid or "",
                    "match_method": exact_res["match_method"],
                    "match_score": exact_res["match_score"],
                    "confidence_level": exact_res["confidence_level"],
                    "review_status": "auto_matched"
                })
                matched_a_indices.add(idx_a)
                matched_b_indices.add(idx_b)
            else:
                remaining_candidates.append((idx_a, idx_b, strategy))

        # Step 2: Multi-Field Fuzzy Matching on remaining pairs
        for idx_a, idx_b, strategy in remaining_candidates:
            if idx_a in matched_a_indices and idx_b in matched_b_indices:
                continue

            row_a = df_a.iloc[idx_a]
            row_b = df_b.iloc[idx_b]

            field_scores = self.fuzzy_matcher.evaluate_pair(row_a, row_b, map_a, map_b)
            composite_score, _ = self.scoring_engine.compute_composite_score(field_scores)
            conf_level, decision = self.confidence_classifier.classify(composite_score, match_method="fuzzy_multi_field")

            off_wid = None
            if map_a.get("work_id"):
                off_wid = row_a.get(map_a["work_id"])
            elif map_b.get("work_id"):
                off_wid = row_b.get(map_b["work_id"])

            if decision == "MATCH":
                can_id = self.provenance_manager.get_or_create_canonical_id(off_wid, ds_name_a, idx_a)
                self.provenance_manager.link_entities(can_id, off_wid, ds_name_b, idx_b)

                matched_records.append({
                    "canonical_work_id": can_id,
                    "source_parliament": self.parliament,
                    "source_dataset": ds_name_a,
                    "source_row_id": idx_a,
                    "matched_dataset": ds_name_b,
                    "matched_row_id": idx_b,
                    "official_work_id": off_wid or "",
                    "match_method": "fuzzy_multi_field",
                    "match_score": composite_score,
                    "confidence_level": conf_level,
                    "review_status": "auto_matched"
                })
                matched_a_indices.add(idx_a)
                matched_b_indices.add(idx_b)

            elif decision == "REVIEW":
                self.review_queue.add_to_review(
                    source_dataset=ds_name_a, source_row_id=idx_a,
                    candidate_dataset=ds_name_b, candidate_row_id=idx_b,
                    source_row=row_a, candidate_row=row_b,
                    map_a=map_a, map_b=map_b,
                    match_score=composite_score,
                    confidence_level=conf_level,
                    match_method="fuzzy_multi_field",
                    field_scores=field_scores
                )

        unresolved_count = len(df_a) - len(matched_a_indices)
        return {
            "dataset_pair": f"{ds_name_a} -> {ds_name_b}",
            "status": "success",
            "candidate_pairs": len(candidates),
            "high_confidence_matches": len(matched_records),
            "review_count": len([q for q in self.review_queue.queue if q["source_dataset"] == ds_name_a]),
            "unresolved_count": unresolved_count,
            "matched_records": matched_records
        }

    def run(self, sample_limit: int = 1500) -> dict:
        """
        Executes complete Entity Resolution workflow for the parliament.
        Exports matches, review queue, unresolved records, and reports.
        """
        start_time = time.time()
        logger.info(f"============================================================")
        logger.info(f"STARTING ENTITY RESOLUTION FOR: {self.parliament.upper()}")
        logger.info(f"============================================================")

        datasets = self.discover_datasets()
        if not datasets:
            logger.warning(f"No suitable work datasets discovered for [{self.parliament.upper()}].")
            return {"status": "no_datasets"}

        logger.info(f"Discovered {len(datasets)} work-level datasets: {list(datasets.keys())}")

        all_matches = []
        pair_stats = []

        # Compare lifecycle pairs in logical relevance order
        # e.g. recommended <-> sanctioned, sanctioned <-> expenditure, sanctioned <-> completed
        ds_keys = list(datasets.keys())
        relevant_pairs = []
        for i in range(len(ds_keys)):
            for j in range(i + 1, len(ds_keys)):
                k1, k2 = ds_keys[i], ds_keys[j]
                # Prioritize pairs containing works/sanctioned/recommended/expenditure/completed
                relevant_pairs.append((k1, k2))

        for k1, k2 in relevant_pairs:
            res = self.resolve_dataset_pair(k1, datasets[k1], k2, datasets[k2], sample_limit=sample_limit)
            if "matched_records" in res:
                all_matches.extend(res["matched_records"])
            pair_stats.append({
                "source_dataset": k1,
                "target_dataset": k2,
                "candidate_pairs_evaluated": res["candidate_pairs"],
                "high_confidence_matches": res["high_confidence_matches"],
                "records_in_review": res["review_count"],
                "unresolved_records": res["unresolved_count"]
            })

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Export Matches CSV
        matches_df = pd.DataFrame(all_matches)
        if matches_df.empty:
            matches_df = pd.DataFrame(columns=[
                "canonical_work_id", "source_parliament", "source_dataset", "source_row_id",
                "matched_dataset", "matched_row_id", "official_work_id", "match_method",
                "match_score", "confidence_level", "review_status"
            ])
        matches_path = self.output_dir / "entity_resolution_matches.csv"
        matches_df.to_csv(matches_path, index=False)
        logger.info(f"Exported matches to: {matches_path} ({len(matches_df)} records)")

        # 2. Export Review Queue CSV
        review_df = self.review_queue.to_dataframe()
        review_path = self.output_dir / "review_queue.csv"
        review_df.to_csv(review_path, index=False)
        logger.info(f"Exported review queue to: {review_path} ({len(review_df)} records)")

        # 3. Export Summary CSV
        summary_path = self.report_generator.generate_summary_csv(pair_stats, self.output_dir)

        total_time = round(time.time() - start_time, 2)
        summary_data = {
            "execution_timestamp": datetime.now().isoformat(),
            "parliament": self.parliament,
            "datasets_discovered": len(datasets),
            "dataset_pairs_compared": len(relevant_pairs),
            "total_high_confidence_matches": len(matches_df),
            "total_records_in_review_queue": len(review_df),
            "processing_time_seconds": total_time,
            "pair_statistics": pair_stats
        }

        report_path = self.report_generator.generate_report(summary_data, self.output_dir)
        logger.info(f"Exported ER report to: {report_path}")
        logger.info(f"============================================================\n")

        return summary_data

def resolve_parliament(parliament: str = "lok_sabha", sample_limit: int = 1500) -> dict:
    """Entrypoint function for single parliament resolution."""
    resolver = EntityResolver(parliament=parliament)
    return resolver.run(sample_limit=sample_limit)

def resolve_all(sample_limit: int = 1500) -> dict:
    """Resolves entities across all parliaments."""
    ls_res = resolve_parliament("lok_sabha", sample_limit=sample_limit)
    rs_res = resolve_parliament("rajya_sabha", sample_limit=sample_limit)
    return {"lok_sabha": ls_res, "rajya_sabha": rs_res}

def main():
    parser = argparse.ArgumentParser(description="NIRIKSHAK-AI Dynamic Entity Resolution Engine")
    parser.add_argument("--parliament", "-p", default="all", choices=["lok_sabha", "rajya_sabha", "all"],
                        help="Parliament scope (lok_sabha, rajya_sabha, or all)")
    parser.add_argument("--limit", "-l", type=int, default=1500,
                        help="Sample limit per dataset for candidate blocking (default 1500)")

    args = parser.parse_args()

    if args.parliament == "all":
        resolve_all(sample_limit=args.limit)
    else:
        resolve_parliament(parliament=args.parliament, sample_limit=args.limit)

if __name__ == "__main__":
    main()

