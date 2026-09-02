import datetime
from sqlalchemy import Column, String, Float, DateTime, Text
from db.session import Base

class PredictiveWorkRisk(Base):
    __tablename__ = "predictive_work_risks"

    canonical_work_id = Column(String, primary_key=True, index=True)
    source_house = Column(String, index=True)
    canonical_state = Column(String, index=True)
    canonical_mp_name = Column(String, index=True)
    canonical_work_category = Column(String, index=True)
    project_risk_score = Column(Float, default=0.0, index=True)
    delay_probability = Column(Float, default=0.0)
    cost_overrun_probability = Column(Float, default=0.0)
    stagnation_probability = Column(Float, default=0.0)
    expected_delay_days = Column(Float, default=0.0)
    risk_category = Column(String, index=True)
    recommended_monitoring_priority = Column(String, index=True)
    top_contributing_factors = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
