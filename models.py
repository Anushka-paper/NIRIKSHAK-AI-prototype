"""
MPLADS Compliance System — Data Model
--------------------------------------
This models the core entities from the MPLADS 2023 Guidelines as a
relational schema. Use this with SQLAlchemy + any DB (SQLite for
prototyping, Postgres for production).

Design principle: every table that a RULE checks against should carry
enough state to answer that rule WITHOUT re-computation across the whole
history every time (i.e. keep running totals on the ledger, don't
recompute sums from scratch on every request once volumes grow).
"""

from datetime import date
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, Float, Date, Boolean, ForeignKey, Enum, Text
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ---------------------------------------------------------------------
# ENUMS — mirror the classifications used throughout the guidelines
# ---------------------------------------------------------------------

class MPType(PyEnum):
    LOK_SABHA = "lok_sabha"
    RAJYA_SABHA_ELECTED = "rajya_sabha_elected"
    RAJYA_SABHA_NOMINATED = "rajya_sabha_nominated"


class WorkStatus(PyEnum):
    RECOMMENDED = "recommended"
    SANCTIONED = "sanctioned"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    UC_FILED = "uc_filed"
    AUDITED = "audited"
    ABANDONED = "abandoned"


class BeneficiaryCategory(PyEnum):
    GENERAL = "general"
    SC = "sc"
    ST = "st"


class UserRole(PyEnum):
    MP = "mp"
    STATE_NODAL = "state_nodal"
    DISTRICT = "district"
    MINISTRY = "ministry"


# ---------------------------------------------------------------------
# CORE ENTITIES
# ---------------------------------------------------------------------

class MemberOfParliament(Base):
    __tablename__ = "mps"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    mp_type = Column(Enum(MPType), nullable=False)
    constituency_name = Column(String)          # for LS MPs
    state = Column(String)                      # for LS / elected RS MPs
    term_start_date = Column(Date, nullable=False)
    term_end_date = Column(Date, nullable=True)  # null if currently serving

    ledgers = relationship("FinancialYearLedger", back_populates="mp")
    works = relationship("WorkRecommendation", back_populates="mp")


class User(Base):
    """
    Login identity for the 4 SIH26102 personas. `scope_id` is what
    every data endpoint filters on:
      - MP           -> mps.id (as a string)
      - STATE_NODAL  -> state name (matches WorkRecommendation.work_location_state)
      - DISTRICT     -> district name (matches WorkRecommendation.work_location_district)
      - MINISTRY     -> null (unrestricted, national scope)

    Accounts are provisioned by a Ministry admin, not self-registered
    (see auth.create_invited_user / POST /admin/users): `password_hash`
    starts null and the account is unusable until the invited user
    accepts their invite and sets their own password
    (POST /auth/accept-invite). This avoids ever having Ministry choose
    or transmit a real password on someone else's behalf.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    scope_id = Column(String, nullable=True)
    created_at = Column(Date, nullable=False)

    invite_token = Column(String, nullable=True, unique=True)
    invite_expires_at = Column(Date, nullable=True)

    # Ministry can deactivate an account (revoke access) without deleting
    # it. Checked on every request, not just at login, so deactivating
    # someone takes effect immediately even on an already-issued JWT.
    is_active = Column(Boolean, default=True, nullable=False)


class ConstituencyBoundary(Base):
    """
    Geospatial reference. In a real system this stores a polygon
    (PostGIS geometry column). For a prototype, store a district/state
    list that approximates the constituency — good enough to validate
    "is this work location inside the MP's jurisdiction".
    """
    __tablename__ = "constituency_boundaries"

    id = Column(Integer, primary_key=True)
    constituency_name = Column(String, nullable=False)
    state = Column(String, nullable=False)
    districts_covered = Column(Text)  # comma-separated for prototype


class FinancialYearLedger(Base):
    """
    One row per MP per Financial Year. This is the single source of
    truth every financial rule checks against — never recompute totals
    by summing WorkRecommendation rows on every request; update this
    ledger transactionally whenever a work is sanctioned.
    """
    __tablename__ = "fy_ledgers"

    id = Column(Integer, primary_key=True)
    mp_id = Column(Integer, ForeignKey("mps.id"), nullable=False)
    financial_year = Column(String, nullable=False)  # e.g. "2025-26"

    base_entitlement = Column(Float, default=50_000_000)   # ₹5 Cr
    tenure_multiplier = Column(Float, default=1.0)         # 0 / 0.5 / 1.0
    prorated_entitlement = Column(Float)                   # computed

    redistributed_balance = Column(Float, default=0.0)     # ex-MP inflow
    interest_accrued = Column(Float, default=0.0)

    cumulative_sanctioned = Column(Float, default=0.0)
    cumulative_disbursed = Column(Float, default=0.0)

    sc_area_sanctioned = Column(Float, default=0.0)
    st_area_sanctioned = Column(Float, default=0.0)

    repair_renovation_sanctioned = Column(Float, default=0.0)
    out_of_constituency_sanctioned = Column(Float, default=0.0)

    mp = relationship("MemberOfParliament", back_populates="ledgers")

    @property
    def total_available(self) -> float:
        return (
            (self.prorated_entitlement or 0.0)
            + (self.redistributed_balance or 0.0)
            + (self.interest_accrued or 0.0)
        )


class Society(Base):
    """Registered societies/trusts/cooperatives — Chapter 6 entities."""
    __tablename__ = "societies"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    darpan_id = Column(String, unique=True)
    registration_date = Column(Date)
    registration_act = Column(String)  # Societies Act / Trusts Act / Co-op Act
    active_since = Column(Date)        # to check 3-year continuous operation

    lifetime_sanctioned_total = Column(Float, default=0.0)  # ₹1 Cr cap tracker

    # Conflict-of-interest: list of MP IDs who are trustees/office bearers
    conflicted_mp_ids = Column(Text)  # comma-separated MP ids for prototype


class WorkRecommendation(Base):
    """
    A single recommended/sanctioned work — the unit every compliance
    check ultimately runs against.
    """
    __tablename__ = "work_recommendations"

    id = Column(Integer, primary_key=True)
    mp_id = Column(Integer, ForeignKey("mps.id"), nullable=False)
    fy_ledger_id = Column(Integer, ForeignKey("fy_ledgers.id"), nullable=False)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)  # feeds the negative-list filter
    estimated_cost = Column(Float, nullable=False)

    beneficiary_category = Column(Enum(BeneficiaryCategory), default=BeneficiaryCategory.GENERAL)
    is_repair_or_renovation = Column(Boolean, default=False)
    is_out_of_constituency = Column(Boolean, default=False)
    is_calamity_relief = Column(Boolean, default=False)

    work_location_district = Column(String)
    work_location_state = Column(String)

    recommendation_date = Column(Date, nullable=False)
    sanction_date = Column(Date, nullable=True)
    completion_deadline = Column(Date, nullable=True)
    actual_completion_date = Column(Date, nullable=True)

    status = Column(Enum(WorkStatus), default=WorkStatus.RECOMMENDED)

    mp = relationship("MemberOfParliament", back_populates="works")


class InspectionRecord(Base):
    """Tracks IA / District / SNA inspection quota compliance."""
    __tablename__ = "inspection_records"

    id = Column(Integer, primary_key=True)
    work_id = Column(Integer, ForeignKey("work_recommendations.id"), nullable=False)
    inspecting_authority = Column(String)  # "IA" / "DISTRICT" / "SNA"
    inspection_date = Column(Date)
    passed = Column(Boolean)
    notes = Column(Text)


class Alert(Base):
    """
    Risk-based alert raised when a rule fires at BLOCK/CRITICAL severity
    against a work. Scoped so each of the 4 personas only sees alerts
    relevant to them — see auth.scope_alerts_query. Epic 2 of
    mdfiles/PRD_GAP_CLOSURE.md.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    work_id = Column(Integer, ForeignKey("work_recommendations.id"), nullable=False)
    rule_code = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # "BLOCK" / "CRITICAL"
    message = Column(Text, nullable=False)

    # Who this alert is for. target_role is always set; target_scope_id
    # narrows it (an MP's id, or a state/district name) — null means
    # "every user of that role" (used for the MINISTRY rollup).
    target_role = Column(Enum(UserRole), nullable=False)
    target_scope_id = Column(String, nullable=True)

    created_at = Column(Date, nullable=False)
    read_at = Column(Date, nullable=True)
    resolved_at = Column(Date, nullable=True)


class RiskExplanation(Base):
    """
    Cache + audit trail for Epic 6's LLM-grounded risk explanation layer
    (ml-service/genai/). Keyed by (work_id, model_version) -- a cache hit
    means "the underlying risk score hasn't changed since we last
    explained it," so there's no reason to pay for a fresh LLM call.
    Stores the full grounding payload alongside the generated text so an
    auditor can see exactly what evidence the explanation was allowed to
    reference (see genai/context.py's build_grounding_payload).
    """
    __tablename__ = "risk_explanations"

    id = Column(Integer, primary_key=True)
    # String, not an FK to work_recommendations: the risk model (Epic 3)
    # predicts over the historical analytics dataset's canonical_work_id
    # (e.g. "CW_LO_006138" from data/features/*/work_features.csv), a
    # separate ID space from this demo DB's small integer-keyed
    # WorkRecommendation table -- see mdfiles/PRD_GAP_CLOSURE.md's note
    # on the two disconnected data domains.
    work_id = Column(String, nullable=False, index=True)
    model_version = Column(String, nullable=False)

    grounding_payload_json = Column(Text, nullable=False)
    why_json = Column(Text, nullable=False)              # JSON list[str]
    recommended_actions_json = Column(Text, nullable=False)  # JSON list[{action, rationale}]
    confidence_note = Column(Text, nullable=False)

    generated_by = Column(String, nullable=False)  # "llm" | "fallback"
    created_at = Column(Date, nullable=False)


class ComplianceCheckLog(Base):
    """
    Audit trail: every automated check run against a work, with the
    rule id, outcome, and message. This is what you show an auditor
    later — "here's every rule this work was checked against and when".
    """
    __tablename__ = "compliance_check_logs"

    id = Column(Integer, primary_key=True)
    work_id = Column(Integer, ForeignKey("work_recommendations.id"), nullable=False)
    rule_id = Column(String, nullable=False)
    para_reference = Column(String)
    passed = Column(Boolean, nullable=False)
    severity = Column(String)  # "BLOCK" / "WARN" / "REVIEW"
    message = Column(Text)
    checked_at = Column(Date)


# ---------------------------------------------------------------------
# COMPLIANCE 2.0 (VANTA / DRATA STYLE CONTINUOUS COMPLIANCE ENTITIES)
# ---------------------------------------------------------------------

class ComplianceControl(Base):
    """
    MPLADS Control Library — mapped to statutory controls C001 - C010.
    """
    __tablename__ = "compliance_controls"

    id = Column(String, primary_key=True)  # e.g., "C001", "C004"
    name = Column(String, nullable=False)
    para_reference = Column(String, nullable=False)
    category = Column(String, nullable=False)  # "Administrative", "Technical", "Financial", "Documentation", "Physical"
    description = Column(Text)
    severity = Column(String, default="HIGH")
    frequency = Column(String, default="Continuous")


class ProjectEvidence(Base):
    """
    Centralized Evidence Repository — maps files/data items to controls.
    """
    __tablename__ = "project_evidence"

    id = Column(Integer, primary_key=True)
    work_id = Column(Integer, ForeignKey("work_recommendations.id"), nullable=False)
    control_id = Column(String, ForeignKey("compliance_controls.id"), nullable=False)
    evidence_type = Column(String, nullable=False)  # "SanctionOrder", "Estimate", "GeotaggedPhoto", "InspectionReport", "UC"
    title = Column(String, nullable=False)
    file_path = Column(String)
    extracted_metadata_json = Column(Text)  # JSON metadata extracted via Document/Image AI
    verified = Column(Boolean, default=True)
    uploaded_at = Column(Date)


class ComplianceFinding(Base):
    """
    Actionable Findings & Remediation Workflows around failed controls.
    """
    __tablename__ = "compliance_findings"

    id = Column(String, primary_key=True)  # e.g., "MPL-1042"
    work_id = Column(Integer, ForeignKey("work_recommendations.id"), nullable=False)
    control_id = Column(String, ForeignKey("compliance_controls.id"), nullable=False)
    problem_summary = Column(Text, nullable=False)
    severity = Column(String, nullable=False)  # "CRITICAL", "HIGH", "MEDIUM"
    status = Column(String, default="OPEN")    # "OPEN", "IN_REMEDIATION", "RESOLVED"
    assigned_officer = Column(String, default="District Authority")
    required_action = Column(Text, nullable=False)
    deadline_date = Column(Date)
    detected_at = Column(Date)
    resolved_at = Column(Date, nullable=True)
    remediation_notes = Column(Text, nullable=True)

