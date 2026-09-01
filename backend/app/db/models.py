from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import enum
# from pgvector.sqlalchemy import Vector # Disabled for local SQLite fallback

Base = declarative_base()

class GeoLevel(enum.Enum):
    state = "state"
    constituency = "constituency"

class ModelStatus(enum.Enum):
    staging = "staging"
    production = "production"
    retired = "retired"

class CandidateStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"

class AlertStatus(enum.Enum):
    open = "open"
    reviewing = "reviewing"
    closed = "closed"


# Master/dimension tables
class Geography(Base):
    __tablename__ = 'geography'
    geo_id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(SQLEnum(GeoLevel), nullable=False)
    name = Column(String, nullable=False)
    parent_geo_id = Column(Integer, ForeignKey('geography.geo_id'), nullable=True)

class MPMaster(Base):
    __tablename__ = 'mp_master'
    mp_id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_name = Column(String, nullable=False)
    house = Column(String, nullable=True) # "Lok Sabha" or "Rajya Sabha"
    state_id = Column(Integer, ForeignKey('geography.geo_id'))
    constituency_id = Column(Integer, ForeignKey('geography.geo_id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MPAlias(Base):
    __tablename__ = 'mp_alias'
    alias_id = Column(Integer, primary_key=True, autoincrement=True)
    mp_id = Column(Integer, ForeignKey('mp_master.mp_id'), nullable=False)
    raw_name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=True)
    confidence_score = Column(Float, default=1.0)
    matching_method = Column(String, default="exact")
    verified = Column(Boolean, default=True)
    source_file = Column(String)

class VendorMaster(Base):
    __tablename__ = 'vendor_master'
    vendor_id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_name = Column(String, nullable=False)
    registration_number = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class VendorAlias(Base):
    __tablename__ = 'vendor_alias'
    alias_id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_id = Column(Integer, ForeignKey('vendor_master.vendor_id'), nullable=False)
    raw_name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=True)
    match_confidence = Column(Float, default=1.0)
    matching_method = Column(String, default="exact")
    verified = Column(Boolean, default=True)

class IDAMaster(Base):
    __tablename__ = 'ida_master'
    ida_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    state_id = Column(Integer, ForeignKey('geography.geo_id'), nullable=True)
    parent_agency_id = Column(Integer, ForeignKey('ida_master.ida_id'), nullable=True)

class IDAAlias(Base):
    __tablename__ = 'ida_alias'
    alias_id = Column(Integer, primary_key=True, autoincrement=True)
    ida_id = Column(Integer, ForeignKey('ida_master.ida_id'), nullable=False)
    raw_name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=True)
    match_confidence = Column(Float, default=1.0)
    matching_method = Column(String, default="exact")
    verified = Column(Boolean, default=True)

class EntityResolutionResult(Base):
    __tablename__ = 'entity_resolution_result'
    result_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String, nullable=False) # work, mp, vendor, ida
    source_record_id = Column(String, nullable=False)
    source_entity_value = Column(String, nullable=False)
    candidate_entity_id = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=False)
    matching_method = Column(String, nullable=False) # exact_id, exact_alias, fuzzy, candidate_scoring
    matching_features = Column(JSON, nullable=True)
    resolution_status = Column(String, nullable=False) # AUTO_RESOLVED, REVIEW_REQUIRED, UNRESOLVED
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EntityResolutionReview(Base):
    __tablename__ = 'entity_resolution_review'
    review_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String, nullable=False)
    source_value = Column(String, nullable=False)
    candidate_id = Column(String, nullable=True)
    candidate_name = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=False)
    reason = Column(String, nullable=True)
    status = Column(String, default="REVIEW_REQUIRED") # AUTO_RESOLVED, REVIEW_REQUIRED, CONFIRMED, REJECTED, UNRESOLVED
    reviewer = Column(String, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    final_decision = Column(String, nullable=True)

# Lifecycle tables
class Allocation(Base):
    __tablename__ = 'allocations'
    allocation_id = Column(Integer, primary_key=True, autoincrement=True)
    mp_id = Column(Integer, ForeignKey('mp_master.mp_id'), nullable=False)
    fiscal_year = Column(String, nullable=False)
    allocated_amount = Column(Integer, nullable=False) # in paise
    source_row_hash = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class WorkRecommended(Base):
    __tablename__ = 'works_recommended'
    work_id = Column(Integer, primary_key=True, autoincrement=True)
    work_id_raw = Column(String, nullable=False)
    house = Column(String, nullable=True) # "Lok Sabha" or "Rajya Sabha"
    mp_id = Column(Integer, ForeignKey('mp_master.mp_id'), nullable=False)
    ida_id = Column(Integer, ForeignKey('ida_master.ida_id'), nullable=False)
    category = Column(String)
    description = Column(String)
    recommended_amount = Column(Integer, nullable=False) # in paise
    recommendation_date = Column(DateTime(timezone=True))
    source_row_hash = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # pgvector embedding for description
    # embedding = Column(Vector(384)) # Disabled for local SQLite fallback
    embedding = Column(JSON) # Fallback to JSON for SQLite

class WorkSanctioned(Base):
    __tablename__ = 'works_sanctioned'
    work_id = Column(Integer, ForeignKey('works_recommended.work_id'), primary_key=True)
    sanctioned_amount = Column(Integer, nullable=False) # in paise
    sanction_date = Column(DateTime(timezone=True))
    source_row_hash = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Expenditure(Base):
    __tablename__ = 'expenditure'
    txn_id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(Integer, ForeignKey('works_recommended.work_id'), nullable=False)
    vendor_id = Column(Integer, ForeignKey('vendor_master.vendor_id'), nullable=False)
    amount = Column(Integer, nullable=False) # in paise
    txn_date = Column(DateTime(timezone=True))
    payment_status = Column(String)
    source_row_hash = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class WorkCompleted(Base):
    __tablename__ = 'works_completed'
    work_id = Column(Integer, ForeignKey('works_recommended.work_id'), primary_key=True)
    completion_date = Column(DateTime(timezone=True))
    status = Column(String)
    has_completion_evidence = Column(Boolean, default=False)
    source_row_hash = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CalamityConsent(Base):
    __tablename__ = 'calamity_consent'
    consent_id = Column(Integer, primary_key=True, autoincrement=True)
    mp_id = Column(Integer, ForeignKey('mp_master.mp_id'), nullable=False)
    calamity_type = Column(String, nullable=False)
    amount = Column(Integer, nullable=False) # in paise
    consent_date = Column(DateTime(timezone=True))
    work_id = Column(Integer, ForeignKey('works_recommended.work_id'), nullable=True)
    source_row_hash = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Feature layer
class FeatureWork(Base):
    __tablename__ = 'features_work'
    work_id = Column(Integer, ForeignKey('works_recommended.work_id'), primary_key=True)
    feature_version = Column(String, nullable=False)
    sanction_delay_days = Column(Integer)
    duration_percentile = Column(Float)
    estimate_variance_pct = Column(Float)
    overrun_pct = Column(Float)
    inactivity_gap_days = Column(Integer)
    computed_at = Column(DateTime(timezone=True), primary_key=True, server_default=func.now())

class FeatureTransaction(Base):
    __tablename__ = 'features_transaction'
    txn_id = Column(Integer, ForeignKey('expenditure.txn_id'), primary_key=True)
    feature_version = Column(String, nullable=False)
    amount_zscore = Column(Float)
    amount_percentile = Column(Float)
    expenditure_to_sanction_pct = Column(Float)
    computed_at = Column(DateTime(timezone=True), primary_key=True, server_default=func.now())

class FeatureVendor(Base):
    __tablename__ = 'features_vendor'
    vendor_id = Column(Integer, ForeignKey('vendor_master.vendor_id'), primary_key=True)
    feature_version = Column(String, nullable=False)
    concentration_pct = Column(Float)
    work_count = Column(Integer)
    constituency_count = Column(Integer)
    computed_at = Column(DateTime(timezone=True), primary_key=True, server_default=func.now())

class FeatureMP(Base):
    __tablename__ = 'features_mp'
    mp_id = Column(Integer, ForeignKey('mp_master.mp_id'), primary_key=True)
    feature_version = Column(String, nullable=False)
    utilisation_pct = Column(Float)
    output_per_rupee = Column(Float)
    computed_at = Column(DateTime(timezone=True), primary_key=True, server_default=func.now())

# Baselines
class Baseline(Base):
    __tablename__ = 'baselines'
    baseline_id = Column(Integer, primary_key=True, autoincrement=True)
    baseline_version = Column(String, nullable=False)
    group_key = Column(String, nullable=False)
    metric = Column(String, nullable=False)
    n_obs = Column(Integer)
    fallback_level = Column(String)
    median = Column(Float)
    p10 = Column(Float)
    p25 = Column(Float)
    p75 = Column(Float)
    p90 = Column(Float)
    p95 = Column(Float)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())

# ML/MLOps
class ModelRegistry(Base):
    __tablename__ = 'model_registry'
    model_id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    training_dataset_version = Column(String)
    feature_version = Column(String)
    hyperparameters = Column(JSON)
    trained_at = Column(DateTime(timezone=True))
    eval_metrics = Column(JSON)
    artifact_path = Column(String)
    code_version = Column(String)
    status = Column(SQLEnum(ModelStatus))

class Prediction(Base):
    __tablename__ = 'predictions'
    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(Integer, ForeignKey('works_recommended.work_id'), nullable=False)
    model_id = Column(Integer, ForeignKey('model_registry.model_id'), nullable=False)
    prediction_type = Column(String, nullable=False)
    value = Column(Float)
    top_contributing_features = Column(JSON)
    predicted_at = Column(DateTime(timezone=True), server_default=func.now())

class AnomalyScore(Base):
    __tablename__ = 'anomaly_scores'
    score_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    model_id = Column(Integer, ForeignKey('model_registry.model_id'), nullable=False)
    score = Column(Float)
    percentile = Column(Float)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())

class DuplicateCandidate(Base):
    __tablename__ = 'duplicate_candidates'
    pair_id = Column(Integer, primary_key=True, autoincrement=True)
    work_id_a = Column(Integer, ForeignKey('works_recommended.work_id'), nullable=False)
    work_id_b = Column(Integer, ForeignKey('works_recommended.work_id'), nullable=False)
    similarity_score = Column(Float)
    context_match = Column(JSON)
    status = Column(SQLEnum(CandidateStatus))

# Risk & alerts
class RiskComponent(Base):
    __tablename__ = 'risk_components'
    component_id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(Integer, ForeignKey('works_recommended.work_id'), nullable=False)
    component_type = Column(String, nullable=False)
    value = Column(Float)
    source_signal_id = Column(Integer)
    baseline_version = Column(String)
    model_id = Column(Integer, ForeignKey('model_registry.model_id'))
    computed_at = Column(DateTime(timezone=True), server_default=func.now())

class RiskScore(Base):
    __tablename__ = 'risk_scores'
    risk_id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(Integer, ForeignKey('works_recommended.work_id'), nullable=False)
    composite_score = Column(Float)
    fusion_model_version = Column(String)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())

class Alert(Base):
    __tablename__ = 'alerts'
    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(Integer, ForeignKey('works_recommended.work_id'), nullable=False)
    severity = Column(String, nullable=False)
    previous_score = Column(Float)
    new_score = Column(Float)
    components = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(SQLEnum(AlertStatus))

class ReviewOutcome(Base):
    __tablename__ = 'review_outcomes'
    review_id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(Integer, ForeignKey('alerts.alert_id'), nullable=False)
    reviewer_id = Column(String, nullable=False)
    decision = Column(String)
    notes = Column(String)
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditLog(Base):
    __tablename__ = 'audit_log'
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String)
    entity_id = Column(Integer)
    action = Column(String)
    actor = Column(String)
    payload = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PipelineRun(Base):
    __tablename__ = 'pipeline_run'
    run_id = Column(Integer, primary_key=True, autoincrement=True)
    source_file = Column(String)
    file_hash = Column(String)
    rows_processed = Column(Integer)
    rows_quarantined = Column(Integer)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True))

class Quarantine(Base):
    __tablename__ = 'quarantine'
    row_id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey('pipeline_run.run_id'), nullable=False)
    raw_payload = Column(JSON)
    reason = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
