import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app_dir = os.path.abspath(os.path.dirname(__file__))

for d in [root_dir, backend_dir, app_dir]:
    if d not in sys.path:
        sys.path.insert(0, d)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1 import (
    dashboard, data_quality, entity_resolution, standardization, 
    compliance, features, predictive, early_warning, trends, vendors, calamity, models, duplicates
)
from core.config import get_cors_origins, settings
from db.bootstrap import ensure_demo_database

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials="*" not in get_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(data_quality.router, prefix="/api/v1/data-quality", tags=["Data Quality"])
app.include_router(standardization.router, prefix="/api/v1", tags=["Data Standardization"])
app.include_router(entity_resolution.router, prefix="/api/v1", tags=["Entity Resolution"])
app.include_router(compliance.router, prefix="/api/v1", tags=["Compliance Engine"])
app.include_router(features.router, prefix="/api/v1", tags=["Canonical Feature Store"])
app.include_router(predictive.router, prefix="/api/v1", tags=["Predictive Modeling Layer"])
app.include_router(early_warning.router, prefix="/api/v1", tags=["Early Warning Engine"])
app.include_router(trends.router, prefix="/api/v1", tags=["Trends & Analytics Layer (§22)"])
app.include_router(vendors.router, prefix="/api/v1", tags=["Vendor Intelligence Layer (§22)"])
app.include_router(calamity.router, prefix="/api/v1", tags=["Calamity Relief Module (§22)"])
app.include_router(models.router, prefix="/api/v1", tags=["Model Monitoring Layer (§22)"])
app.include_router(duplicates.router, prefix="/api/v1", tags=["Duplicate Payment Detector (§10, §11)"])

@app.on_event("startup")
def startup_event():
    ensure_demo_database()
    print("[NIRIKSHAK AI] Database initialized successfully.")

@app.get("/")
def read_root():
    return {"message": "NIRIKSHAK AI API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
