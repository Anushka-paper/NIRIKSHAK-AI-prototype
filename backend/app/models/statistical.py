import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from db.session import Base

class StatisticalBaseline(Base):
    __tablename__ = "statistical_baselines"

    peer_group_key = Column(String, primary_key=True, index=True)
    category = Column(String, index=True)
    state = Column(String, index=True)
    size_tier = Column(String, index=True)
    peer_count = Column(Integer, default=0)
    exp_mean = Column(Float, default=0.0)
    exp_std = Column(Float, default=0.0)
    exp_q1 = Column(Float, default=0.0)
    exp_q3 = Column(Float, default=0.0)
    exp_iqr = Column(Float, default=0.0)
    exp_upper_fence = Column(Float, default=0.0)
    exp_lower_fence = Column(Float, default=0.0)
    delay_mean = Column(Float, default=0.0)
    delay_std = Column(Float, default=0.0)
    delay_upper_fence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class StatisticalAnomaly(Base):
    __tablename__ = "statistical_anomalies"

    canonical_work_id = Column(String, primary_key=True, index=True)
    peer_group_key = Column(String, index=True)
    project_size_tier = Column(String, index=True)
    expenditure_amount_inr = Column(Float, default=0.0)
    sanction_delay_days = Column(Float, nullable=True)
    amount_zscore = Column(Float, default=0.0)
    delay_zscore = Column(Float, default=0.0)
    iqr_amount_outlier = Column(Boolean, default=False)
    iqr_delay_outlier = Column(Boolean, default=False)
    zscore_outlier = Column(Boolean, default=False)
    statistical_anomaly_score = Column(Float, default=0.0)
    is_statistical_anom = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
