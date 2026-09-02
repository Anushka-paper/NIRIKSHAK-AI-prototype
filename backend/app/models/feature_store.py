import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey
from db.session import Base

class FeaturesWork(Base):
    __tablename__ = "features_work"
    
    canonical_work_id = Column(String, primary_key=True, index=True)
    source_house = Column(String, index=True)
    canonical_state = Column(String, index=True)
    canonical_constituency = Column(String, index=True)
    canonical_mp_name = Column(String, index=True)
    canonical_work_category = Column(String, index=True)
    sanction_delay_days = Column(Float, nullable=True)
    completion_delay_days = Column(Float, nullable=True)
    inactivity_gap_days = Column(Float, nullable=True)
    duration_percentile = Column(Float, nullable=True)
    estimate_variance_pct = Column(Float, nullable=True)
    overrun_pct = Column(Float, nullable=True)
    has_recommendation = Column(Boolean, default=False)
    has_sanction = Column(Boolean, default=False)
    has_expenditure = Column(Boolean, default=False)
    has_completion = Column(Boolean, default=False)
    lifecycle_completeness_ratio = Column(Float, default=0.25)
    lifecycle_stage = Column(String, index=True)
    text_length_char = Column(Integer, default=0)
    text_word_count = Column(Integer, default=0)
    feature_version = Column(String, default="v1.0")
    computed_at = Column(DateTime, default=datetime.datetime.utcnow)
    row_hash = Column(String, nullable=True)

class FeaturesTransaction(Base):
    __tablename__ = "features_transaction"
    
    transaction_id = Column(String, primary_key=True, index=True)
    canonical_work_id = Column(String, ForeignKey("features_work.canonical_work_id"), index=True)
    canonical_vendor_name = Column(String, index=True)
    expenditure_amount_inr = Column(Float, default=0.0)
    amount_zscore = Column(Float, nullable=True)
    amount_percentile = Column(Float, nullable=True)
    expenditure_to_sanction_pct = Column(Float, nullable=True)
    is_round_amount = Column(Boolean, default=False)
    days_since_sanction = Column(Float, nullable=True)
    days_to_completion = Column(Float, nullable=True)
    feature_version = Column(String, default="v1.0")
    computed_at = Column(DateTime, default=datetime.datetime.utcnow)

class FeaturesVendor(Base):
    __tablename__ = "features_vendor"
    
    vendor_id = Column(String, primary_key=True, index=True)
    canonical_name = Column(String, index=True)
    canonical_state = Column(String, nullable=True)
    work_count = Column(Integer, default=0)
    constituency_count = Column(Integer, default=0)
    mp_count = Column(Integer, default=0)
    total_expenditure_inr = Column(Float, default=0.0)
    avg_work_value_inr = Column(Float, default=0.0)
    single_mp_dependence_pct = Column(Float, default=100.0)
    concentration_pct = Column(Float, default=0.0)
    feature_version = Column(String, default="v1.0")
    computed_at = Column(DateTime, default=datetime.datetime.utcnow)

class FeaturesMP(Base):
    __tablename__ = "features_mp"
    
    mp_id = Column(String, primary_key=True, index=True)
    canonical_name = Column(String, index=True)
    source_house = Column(String, index=True)
    canonical_state = Column(String, nullable=True)
    recommendation_count = Column(Integer, default=0)
    sanction_count = Column(Integer, default=0)
    completed_count = Column(Integer, default=0)
    total_expenditure_inr = Column(Float, default=0.0)
    utilisation_pct = Column(Float, default=0.0)
    output_per_rupee = Column(Float, default=0.0)
    avg_sanction_delay_days = Column(Float, default=0.0)
    category_entropy = Column(Float, default=0.0)
    top_vendor_concentration_pct = Column(Float, default=0.0)
    feature_version = Column(String, default="v1.0")
    computed_at = Column(DateTime, default=datetime.datetime.utcnow)
