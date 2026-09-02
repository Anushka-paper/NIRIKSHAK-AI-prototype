import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Text
from db.session import Base

class ComplianceViolation(Base):
    __tablename__ = "compliance_violations"

    violation_id = Column(String, primary_key=True, index=True)
    rule_code = Column(String, nullable=False, index=True)
    rule_name = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, index=True) # CRITICAL, HIGH, MEDIUM, LOW
    weight = Column(Integer, default=10)
    entity_type = Column(String, nullable=False) # WORK, TRANSACTION
    entity_id = Column(String, nullable=False, index=True)
    source_house = Column(String, nullable=True)
    state = Column(String, nullable=True)
    mp_name = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
