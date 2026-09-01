import sys
import os
import threading
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.v1 import dashboard, data_quality, live_sync, standardization, entity_resolution
from db.session import SessionLocal
from ingestion.live_sync import sync_live_data

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(data_quality.router, prefix="/api/v1/data-quality", tags=["Data Quality"])
app.include_router(live_sync.router, prefix="/api/v1/sync", tags=["Live Sync"])
app.include_router(standardization.router, prefix="/api/v1", tags=["Data Standardization"])
app.include_router(entity_resolution.router, prefix="/api/v1", tags=["Entity Resolution"])

def background_live_sync_loop():
    """Continuous background daemon syncing live eSAKSHI data every 60 seconds."""
    while True:
        try:
            db = SessionLocal()
            sync_live_data(db, house_filter="all")
            db.close()
        except Exception as e:
            print(f"[Background Live Sync Error]: {e}")
        time.sleep(60)

@app.on_event("startup")
def start_background_live_sync():
    t = threading.Thread(target=background_live_sync_loop, daemon=True)
    t.start()
    print("[NIRIKSHAK AI] Background Dynamic Live Sync Daemon Started (Polling every 60s)!")

@app.get("/")
def read_root():
    return {
        "message": "NIRIKSHAK AI Dynamic Backend Engine Running",
        "live_daemon": "active",
        "sync_interval_seconds": 60
    }
