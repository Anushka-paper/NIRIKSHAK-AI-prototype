import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class MPMaster(Base):
    __tablename__ = "mp_master"
    
    mp_id = Column(String, primary_key=True, index=True)
    canonical_name = Column(String, nullable=False, index=True)
    normalized_name = Column(String, nullable=False, index=True)
    source_house = Column(String, nullable=False)
    canonical_state = Column(String, nullable=True)
    canonical_constituency = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class MPAlias(Base):
    __tablename__ = "mp_alias"
    
    alias_id = Column(String, primary_key=True, index=True)
    mp_id = Column(String, ForeignKey("mp_master.mp_id"), nullable=False)
    original_name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=False)
    confidence_score = Column(Float, default=1.0)
    verified = Column(Boolean, default=True)

class VendorMaster(Base):
    __tablename__ = "vendor_master"
    
    vendor_id = Column(String, primary_key=True, index=True)
    canonical_name = Column(String, nullable=False, index=True)
    normalized_name = Column(String, nullable=False, index=True)
    canonical_state = Column(String, nullable=True)
    total_expenditure_inr = Column(Float, default=0.0)
    works_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class VendorAlias(Base):
    __tablename__ = "vendor_alias"
    
    alias_id = Column(String, primary_key=True, index=True)
    vendor_id = Column(String, ForeignKey("vendor_master.vendor_id"), nullable=False)
    original_name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=False)
    confidence_score = Column(Float, default=1.0)
    verified = Column(Boolean, default=True)

class IDAMaster(Base):
    __tablename__ = "ida_master"
    
    ida_id = Column(String, primary_key=True, index=True)
    canonical_name = Column(String, nullable=False, index=True)
    normalized_name = Column(String, nullable=False, index=True)
    agency_type = Column(String, default="DISTRICT_AUTHORITY")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class IDAAlias(Base):
    __tablename__ = "ida_alias"
    
    alias_id = Column(String, primary_key=True, index=True)
    ida_id = Column(String, ForeignKey("ida_master.ida_id"), nullable=False)
    original_name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=False)
    confidence_score = Column(Float, default=1.0)
    verified = Column(Boolean, default=True)

class EntityResolutionReview(Base):
    __tablename__ = "entity_resolution_review"
    
    review_id = Column(String, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)
    source_value = Column(String, nullable=False)
    candidate_id = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=False)
    status = Column(String, default="REVIEW_REQUIRED") # REVIEW_REQUIRED, CONFIRMED, REJECTED
    final_decision = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

