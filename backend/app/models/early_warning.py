from sqlalchemy import Column, String, Float, Integer, DateTime, Text
from datetime import datetime
from db.session import Base

class EarlyWarningAlert(Base):
    __tablename__ = "early_warning_alerts"

    alert_id = Column(String, primary_key=True, index=True)
    canonical_work_id = Column(String, index=True)
    source_house = Column(String)
    canonical_state = Column(String)
    canonical_mp_name = Column(String)
    priority = Column(String, index=True)
    project_risk_score = Column(Float)
    delay_probability = Column(Float)
    expected_delay_days = Column(Integer)
    status = Column(String, default="NEW", index=True)
    evidence_json = Column(Text)
    auditor_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

