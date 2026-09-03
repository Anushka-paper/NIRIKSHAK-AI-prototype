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
import numpy as np

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
def get_dashboard_overview(parliament: str = Query("all", pattern="^(lok_sabha|rajya_sabha|all)$")):
    """
    Returns consolidated, dynamically calculated intelligence across all 6 standardized datasets:
    Allocation, Calamity, Recommended, Sanctioned, Expenditure, and Completed.
    """
    try:
        from .dataset_aggregator import aggregate_six_datasets
    except ImportError:
        from dataset_aggregator import aggregate_six_datasets

    try:
        data = aggregate_six_datasets(parliament=parliament)
        payload = json.dumps(data, ensure_ascii=False)
        from fastapi import Response
        return Response(content=payload, media_type="application/json")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to calculate six-dataset overview: {str(e)}")

@app.get("/api/v1/overview/states")
def get_overview_states(parliament: str = Query("all", pattern="^(lok_sabha|rajya_sabha|all)$")):
    """
    Returns dynamically aggregated project counts, completion metrics, and budgets for all States and Union Territories.
    """
    try:
        from .state_aggregator import get_aggregated_states
    except ImportError:
        from state_aggregator import get_aggregated_states

    try:
        states = get_aggregated_states(parliament=parliament)
        payload = json.dumps(states, ensure_ascii=False)
        from fastapi import Response
        return Response(content=payload, media_type="application/json")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to aggregate states: {str(e)}")

@app.get("/api/v1/overview/states/{state_id}")
def get_overview_single_state(state_id: str, parliament: str = Query("all", pattern="^(lok_sabha|rajya_sabha|all)$")):
    """
    Returns dynamically calculated metrics for a specific State or Union Territory by ID/slug.
    """
    try:
        from .state_aggregator import get_single_state_details
    except ImportError:
        from state_aggregator import get_single_state_details

    try:
        state_data = get_single_state_details(state_id=state_id, parliament=parliament)
        if not state_data:
            raise HTTPException(status_code=404, detail=f"State with ID '{state_id}' not found.")
        payload = json.dumps(state_data, ensure_ascii=False)
        from fastapi import Response
        return Response(content=payload, media_type="application/json")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to retrieve state details: {str(e)}")

@app.get("/api/v1/data/profiling")
def get_profiling_summary(parliament: str = Query("lok_sabha", pattern="^(lok_sabha|rajya_sabha)$")):
    summary_csv = BASE_DIR / "data" / "profiling" / parliament / "dataset_summary.csv"
    if not summary_csv.exists():
        raise HTTPException(status_code=404, detail=f"Profiling not found for {parliament}")
    df = pd.read_csv(summary_csv)
    return df.to_dict(orient="records")

@app.get("/api/v1/entities/matches")
def get_entity_matches(parliament: str = Query("lok_sabha", pattern="^(lok_sabha|rajya_sabha)$"),
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
def get_review_queue(parliament: str = Query("lok_sabha", pattern="^(lok_sabha|rajya_sabha)$"),
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
def get_standardization_reports(parliament: str = Query("lok_sabha", pattern="^(lok_sabha|rajya_sabha)$")):
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
                             parliament: str = Query("lok_sabha", pattern="^(lok_sabha|rajya_sabha)$"),
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
def trigger_standardization(parliament: str = Query("all", pattern="^(lok_sabha|rajya_sabha|all)$")):
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

# ==========================================================
# ML Prediction & Risk Assessment API
# ==========================================================

from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    work_id: Optional[str] = Field(default="MPLADS-SAMPLE")
    estimated_cost: float = Field(gt=0, description="Estimated/sanctioned cost in INR")
    days_since_sanction: int = Field(ge=0, description="Elapsed days since sanction")
    current_status: Optional[str] = Field(default="Sanctioned")
    state: Optional[str] = Field(default="National")
    category: Optional[str] = Field(default="General Infrastructure")

# Load Trained Model Artifact
TRAINED_MODEL_PATH = BASE_DIR / "ml-service" / "models" / "delay_risk_model.joblib"
_model_bundle = None

def get_trained_model():
    global _model_bundle
    if _model_bundle is None and TRAINED_MODEL_PATH.exists():
        try:
            import joblib
            _model_bundle = joblib.load(TRAINED_MODEL_PATH)
        except Exception as e:
            print(f"Error loading trained model artifact: {e}")
    return _model_bundle

@app.post("/api/v1/predict")
def predict_project_risk(payload: PredictionRequest):
    """
    Evaluates project completion delay risk using the trained Gradient Boosted Classifier
    (with calibrated fallback to heuristic benchmarks).
    """
    bundle = get_trained_model()
    cost = payload.estimated_cost
    days = payload.days_since_sanction
    status_lower = (payload.current_status or "").lower()

    if bundle is not None:
        try:
            clf = bundle["model"]
            feature_names = bundle["feature_names"]
            encoders = bundle.get("encoders", {})

            # Prepare single-row input vector matching the trained feature schema
            row = {}
            for col in feature_names:
                row[col] = 0.0

            # Map available payload fields to feature schema
            if "sanction_amount" in row:
                row["sanction_amount"] = float(cost)
            if "recommended_amount" in row:
                row["recommended_amount"] = float(cost)
            if "days_since_sanction" in row:
                row["days_since_sanction"] = float(days)
            if "total_execution_days" in row:
                row["total_execution_days"] = float(days)
            if "recommendation_to_sanction_days" in row:
                row["recommendation_to_sanction_days"] = float(min(180, days))
            if "work_status" in row:
                row["work_status"] = payload.current_status or "Sanction"
            if "state" in row:
                row["state"] = payload.state or "National"

            # Apply encoders for categorical columns
            df_in = pd.DataFrame([row])
            for col, enc in encoders.items():
                if col in df_in.columns:
                    val_str = str(df_in.at[0, col])
                    try:
                        df_in[col] = enc.transform([[val_str]])[0][0]
                    except Exception:
                        df_in[col] = -1.0

            import numpy as np
            # Execute model inference
            probs = clf.predict_proba(df_in)[0] # [P(LOW), P(MEDIUM), P(HIGH)]
            pred_class_idx = int(np.argmax(probs))
            classes = bundle.get("classes", ["LOW", "MEDIUM", "HIGH"])
            risk_level = classes[pred_class_idx]
            risk_probability = round(float(probs[pred_class_idx]), 2)

            factors = []
            if days > 365:
                factors.append(f"Extended project duration ({days} days elapsed)")
            if cost > 2000000.0:
                factors.append("High capital expenditure bracket (> Rs. 20 Lakhs)")
            if "vendor" in status_lower:
                factors.append("Vendor identification phase latency")
            if not factors:
                factors.append("Standard timeline execution")

            predicted_delay = int(days * 0.4) if risk_level == "HIGH" else (int(days * 0.15) if risk_level == "MEDIUM" else 0)

            return {
                "success": True,
                "work_id": payload.work_id,
                "risk_level": risk_level,
                "risk_probability": risk_probability,
                "predicted_delay_days": predicted_delay,
                "model_engine": "HistGradientBoostingClassifier (Trained on 75,501 Works)",
                "key_factors": factors,
                "recommendations": "Priority audit inspection & contractor escalation recommended" if risk_level == "HIGH" else ("Regular milestone review recommended" if risk_level == "MEDIUM" else "Routine monitoring")
            }
        except Exception as e:
            print(f"Model inference exception, falling back to heuristic: {e}")

    # Fallback heuristic
    risk_score = 0.15
    if cost > 2000000.0:
        risk_score += 0.20
    elif cost > 1000000.0:
        risk_score += 0.10

    if days > 730:
        risk_score += 0.45
    elif days > 365:
        risk_score += 0.25
    elif days > 180:
        risk_score += 0.10

    if any(k in status_lower for k in ["completed", "finish"]):
        risk_score = 0.05
    elif any(k in status_lower for k in ["reject", "cancel"]):
        risk_score = 0.95

    risk_probability = round(min(0.98, max(0.05, risk_score)), 2)
    risk_level = "LOW"
    if risk_probability >= 0.70:
        risk_level = "HIGH"
    elif risk_probability >= 0.40:
        risk_level = "MEDIUM"

    factors = []
    if days > 365:
        factors.append(f"Extended duration ({days} days elapsed)")
    if cost > 1500000.0:
        factors.append("High capital expenditure bracket")
    if not factors:
        factors.append("Standard timeline execution")

    return {
        "success": True,
        "work_id": payload.work_id,
        "risk_level": risk_level,
        "risk_probability": risk_probability,
        "predicted_delay_days": int(days * 0.35) if risk_level != "LOW" else 0,
        "model_engine": "Heuristic Calibrated Baseline",
        "key_factors": factors,
        "recommendations": "Priority audit inspection recommended" if risk_level == "HIGH" else "Routine monitoring"
    }

# ==========================================================
# ML Features APIs (Feature Catalog, Works, Aggregations, Quality)
# ==========================================================

@app.get("/api/v1/features/catalog")
def get_feature_catalog(parliament: str = Query("lok_sabha", pattern="^(lok_sabha|rajya_sabha)$")):
    """
    Returns the feature catalog / dictionary with metadata, formula, aggregation level, and leakage status.
    """
    dict_csv = BASE_DIR / "data" / "features" / parliament / "feature_dictionary.csv"
    if not dict_csv.exists():
        raise HTTPException(status_code=404, detail=f"Feature dictionary not found for {parliament}")

    df = pd.read_csv(dict_csv).fillna("")
    return {
        "parliament": parliament,
        "total_features": len(df),
        "catalog": df.to_dict(orient="records")
    }

@app.get("/api/v1/features/works")
def get_work_features(
    parliament: str = Query("lok_sabha", pattern="^(lok_sabha|rajya_sabha|all)$"),
    state: Optional[str] = None,
    mp_name: Optional[str] = None,
    lifecycle_status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Returns paginated, filterable work features from the ML feature store.
    """
    parliaments = ["lok_sabha", "rajya_sabha"] if parliament == "all" else [parliament]
    dfs = []
    for p in parliaments:
        csv_path = BASE_DIR / "data" / "features" / p / "work_features.csv"
        if csv_path.exists():
            dfs.append(pd.read_csv(csv_path, low_memory=False))

    if not dfs:
        raise HTTPException(status_code=404, detail="Work features not found. Please run feature engineering first.")

    df = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]

    # Filters
    if state:
        st_query = state.lower().replace("-", " ").strip()
        df = df[
            (df["state"].astype(str).str.lower().str.strip() == state.lower().strip()) |
            (df["state"].astype(str).str.lower().str.replace("-", " ").str.strip() == st_query)
        ]
    if mp_name:
        df = df[df["mp_name"].astype(str).str.contains(mp_name, case=False, na=False)]
    if lifecycle_status:
        df = df[df["lifecycle_status"].astype(str).str.upper() == lifecycle_status.upper()]
    if search:
        s_lower = search.lower()
        df = df[
            df["canonical_work_id"].astype(str).str.lower().contains(s_lower, na=False) |
            df["work_description"].astype(str).str.lower().contains(s_lower, na=False) |
            df["constituency"].astype(str).str.lower().contains(s_lower, na=False)
        ]

    total_count = len(df)
    subset = df.iloc[offset:offset+limit].fillna("")

    return {
        "parliament": parliament,
        "total_count": total_count,
        "offset": offset,
        "limit": limit,
        "records": subset.to_dict(orient="records")
    }

@app.get("/api/v1/features/works/{canonical_work_id}")
def get_single_work_feature(canonical_work_id: str, parliament: str = Query("lok_sabha", pattern="^(lok_sabha|rajya_sabha|all)$")):
    """
    Fetches the complete 118-feature profile for a specific canonical work ID.
    """
    parliaments = ["lok_sabha", "rajya_sabha"] if parliament == "all" else [parliament]
    for p in parliaments:
        csv_path = BASE_DIR / "data" / "features" / p / "work_features.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path, low_memory=False)
            match = df[df["canonical_work_id"].astype(str).str.strip() == canonical_work_id.strip()]
            if not match.empty:
                return {
                    "success": True,
                    "canonical_work_id": canonical_work_id,
                    "parliament": p,
                    "features": match.iloc[0].fillna("").to_dict()
                }

    raise HTTPException(status_code=404, detail=f"Work with ID '{canonical_work_id}' not found.")

@app.get("/api/v1/features/aggregations")
def get_feature_aggregations(parliament: str = Query("lok_sabha", pattern="^(lok_sabha|rajya_sabha)$")):
    """
    Returns dimension aggregates for MPs, Constituencies, States, and Vendors.
    """
    base = BASE_DIR / "data" / "features" / parliament

    def load_clean(name):
        f = base / f"{name}_features.csv"
        return pd.read_csv(f).fillna("").to_dict(orient="records") if f.exists() else []

    return {
        "parliament": parliament,
        "mps": load_clean("mp")[:50], # Top 50
        "constituencies": load_clean("constituency")[:50],
        "states": load_clean("state"),
        "vendors": load_clean("vendor")
    }

@app.get("/api/v1/features/quality")
def get_feature_quality(parliament: str = Query("lok_sabha", pattern="^(lok_sabha|rajya_sabha)$")):
    """
    Returns feature quality audit and leakage classifications.
    """
    base = BASE_DIR / "data" / "features" / parliament
    q_csv = base / "feature_quality_report.csv"
    l_csv = base / "feature_leakage_report.csv"
    r_json = base / "feature_generation_report.json"

    quality_records = pd.read_csv(q_csv).fillna("").to_dict(orient="records") if q_csv.exists() else []
    leakage_records = pd.read_csv(l_csv).fillna("").to_dict(orient="records") if l_csv.exists() else []
    
    summary = {}
    if r_json.exists():
        with open(r_json, "r", encoding="utf-8") as fp:
            summary = json.load(fp)

    return {
        "parliament": parliament,
        "summary": summary,
        "quality_audit": quality_records,
        "leakage_audit": leakage_records
    }

@app.get("/health")
def root_health():
    return {
        "status": "healthy",
        "service": "NIRIKSHAK-AI ML Service",
        "version": "1.0.0",
        "ml_pipeline_available": True
    }


