import yaml
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "NIRIKSHAK AI"
    environment: str = "development"
    database_url: str = "sqlite:///../../nirikshak.db"
    redis_url: str = "sqlite://"
    celery_broker_url: str = ""
    celery_result_backend: str = ""
    mlflow_tracking_uri: str = ""
    
    # Thresholds
    cost_overrun_pct: float = 15.0
    sanction_delay_days_max: int = 90
    inactivity_gap_days_max: int = 180
    expenditure_before_sanction_tolerance: int = 0
    duplicate_nlp_similarity_threshold: float = 0.85
    vendor_concentration_max_pct: float = 40.0

    # Risk Weights
    cost_risk: float = 0.20
    delay_risk: float = 0.15
    vendor_risk: float = 0.20
    duplicate_risk: float = 0.25
    compliance_risk: float = 0.20

    class Config:
        env_file = ".env"

settings = Settings()

# Note: In a full implementation, this file would load values from config/*.yaml
# files if present, overriding defaults and env vars according to Phase 0 constraints.
