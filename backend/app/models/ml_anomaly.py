import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text
from db.session import Base

class MLAnomalyScore(Base):
    __tablename__ = "ml_anomaly_scores"

    canonical_work_id = Column(String, primary_key=True, index=True)
    iso_forest_raw_score = Column(Float, default=0.0)
    lof_raw_score = Column(Float, default=0.0)
    ml_anomaly_score = Column(Float, default=0.0, index=True)
    is_ml_anomaly = Column(Boolean, default=False, index=True)
    top_contributing_features = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
