from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import get_cors_origins, settings
from api.v1 import dashboard
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

@app.get("/")
def read_root():
    return {"message": "NIRIKSHAK AI API Stub"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
def startup():
    ensure_demo_database()
