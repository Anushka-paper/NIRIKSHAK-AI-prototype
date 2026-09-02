from sqlalchemy import Column, String, Float, Boolean, DateTime
from datetime import datetime
from db.session import Base

class DuplicatePaymentRecord(Base):
    __tablename__ = "duplicate_payment_records"

    duplicate_id = Column(String, primary_key=True, index=True)
    layer_type = Column(String, index=True) # EXACT, NEAR, REPEATED_AMOUNT, SAMEDAY_VENDOR
    canonical_work_id = Column(String, index=True)
    vendor_name = Column(String, index=True)
    amount_inr = Column(Float)
    transaction_date = Column(String)
    rate_card_baseline_flag = Column(Boolean, default=False)
    contextual_validation_notes = Column(String)
    severity = Column(String, default="HIGH")
    status = Column(String, default="NEW", index=True) # NEW, CONFIRMED_DUPLICATE, LEGITIMATE_RATE_CARD, REJECTED
    auditor_notes = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

