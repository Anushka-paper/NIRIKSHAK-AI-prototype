"""
NIRIKSHAK-AI FastAPI Backend Service.
Provides REST APIs for:
- Executive Dashboard Overview (/api/v1/dashboard/overview)
- Data Quality & Profiling Summary (/api/v1/data/profiling)
- Entity Resolution Results & Review Queue (/api/v1/entities/matches, /api/v1/entities/review-queue)
- Pipeline Status (/api/v1/pipeline/status)
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="NIRIKSHAK-AI Backend API",
    description="FastAPI Backend for NIRIKSHAK-AI MPLADS Monitoring & Irregularity Detection Platform",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "service": "NIRIKSHAK-AI Backend Service",
        "status": "online",
        "docs_url": "/docs",
        "version": "1.0.0"
    }

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/pipeline/status")
def get_pipeline_status():
    summary_path = BASE_DIR / "data" / "pipeline_summary.json"
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="Pipeline has not been executed yet")
    with open(summary_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/v1/dashboard/overview")
def get_dashboard_overview(parliament: str = Query("all", regex="^(lok_sabha|rajya_sabha|all)$")):
    summary_path = BASE_DIR / "data" / "pipeline_summary.json"
    status_data = {}
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            status_data = json.load(f)

    # Calculate aggregate metrics across standardized datasets
    parliaments = ["lok_sabha", "rajya_sabha"] if parliament == "all" else [parliament]
    total_datasets = 0
    total_records = 0

    for par in parliaments:
        std_dir = BASE_DIR / "data" / "standardized" / par
        if std_dir.exists():
            for f in std_dir.glob("*_standardized.csv"):
                total_datasets += 1
                try:
                    # Quick line count without loading whole file
                    with open(f, "rb") as fp:
                        lines = sum(1 for _ in fp) - 1
                        total_records += max(0, lines)
                except Exception:
                    pass

    return {
        "parliament_scope": parliament,
        "total_datasets_monitored": total_datasets,
        "total_records_processed": total_records,
        "pipeline_execution": status_data.get("execution_timestamp"),
        "total_processing_time_seconds": status_data.get("total_processing_time_seconds", 0)
    }

@app.get("/api/v1/data/profiling")
def get_profiling_summary(parliament: str = Query("lok_sabha", regex="^(lok_sabha|rajya_sabha)$")):
    summary_csv = BASE_DIR / "data" / "profiling" / parliament / "dataset_summary.csv"
    if not summary_csv.exists():
        raise HTTPException(status_code=404, detail=f"Profiling not found for {parliament}")
    df = pd.read_csv(summary_csv)
    return df.to_dict(orient="records")

@app.get("/api/v1/entities/matches")
def get_entity_matches(parliament: str = Query("lok_sabha", regex="^(lok_sabha|rajya_sabha)$"),
                       limit: int = 100, offset: int = 0):
    matches_csv = BASE_DIR / "data" / "entity_resolution" / parliament / "entity_resolution_matches.csv"
    if not matches_csv.exists():
        raise HTTPException(status_code=404, detail=f"Entity matches not found for {parliament}")
    df = pd.read_csv(matches_csv)
    total_count = len(df)
    subset = df.iloc[offset:offset+limit].fillna("")
    return {
        "total_matches": total_count,
        "offset": offset,
        "limit": limit,
        "records": subset.to_dict(orient="records")
    }

@app.get("/api/v1/entities/review-queue")
def get_review_queue(parliament: str = Query("lok_sabha", regex="^(lok_sabha|rajya_sabha)$"),
                     limit: int = 100, offset: int = 0):
    queue_csv = BASE_DIR / "data" / "entity_resolution" / parliament / "review_queue.csv"
    if not queue_csv.exists():
        raise HTTPException(status_code=404, detail=f"Review queue not found for {parliament}")
    df = pd.read_csv(queue_csv)
    total_count = len(df)
    subset = df.iloc[offset:offset+limit].fillna("")
    return {
        "total_in_review": total_count,
        "offset": offset,
        "limit": limit,
        "records": subset.to_dict(orient="records")
    }

# ==========================================================
# Data Standardisation APIs
# ==========================================================

@app.get("/api/v1/standardization/reports")
def get_standardization_reports(parliament: str = Query("lok_sabha", regex="^(lok_sabha|rajya_sabha)$")):
    """
    Returns audit transformation reports for all standardized datasets in the parliament.
    """
    std_dir = BASE_DIR / "data" / "standardized" / parliament
    if not std_dir.exists():
        raise HTTPException(status_code=404, detail=f"Standardized data directory not found for {parliament}")

    reports = {}
    for rep_file in std_dir.glob("*_report.json"):
        dataset_name = rep_file.stem.replace("_standardized_report", "").replace("_report", "")
        with open(rep_file, "r", encoding="utf-8") as f:
            reports[dataset_name] = json.load(f)

    return {
        "parliament": parliament,
        "total_reports": len(reports),
        "reports": reports
    }

@app.get("/api/v1/standardization/dataset/{dataset_name}")
def get_standardized_dataset(dataset_name: str,
                             parliament: str = Query("lok_sabha", regex="^(lok_sabha|rajya_sabha)$"),
                             limit: int = 100, offset: int = 0):
    """
    Returns paginated rows from a standardized clean dataset.
    """
    std_dir = BASE_DIR / "data" / "standardized" / parliament
    matched_files = list(std_dir.glob(f"*{dataset_name}*_standardized.csv"))
    if not matched_files:
        raise HTTPException(status_code=404, detail=f"Standardized dataset '{dataset_name}' not found for {parliament}")

    csv_path = matched_files[0]
    df = pd.read_csv(csv_path, low_memory=False)
    total_rows = len(df)
    subset = df.iloc[offset:offset+limit].fillna("")

    return {
        "dataset_name": dataset_name,
        "file_name": csv_path.name,
        "parliament": parliament,
        "total_rows": total_rows,
        "offset": offset,
        "limit": limit,
        "records": subset.to_dict(orient="records")
    }

@app.post("/api/v1/standardization/run")
def trigger_standardization(parliament: str = Query("all", regex="^(lok_sabha|rajya_sabha|all)$")):
    """
    Triggers dynamic data standardisation on raw datasets.
    """
    sys.path.insert(0, str(BASE_DIR / "ml-service"))
    from preprocessing.standardization.standardizer import standardize_directory

    raw_dir = BASE_DIR / "data" / "raw"
    out_dir = BASE_DIR / "data" / "standardized"

    try:
        results = standardize_directory(input_dir=raw_dir, output_dir=out_dir, parliament=parliament)
        return {
            "status": "success",
            "message": f"Standardisation completed successfully for {parliament}",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Standardisation failed: {str(e)}")

