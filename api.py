"""
FastAPI layer over the compliance engine with DB persistence & Human Review Workflow.
"""

from datetime import date
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models import (
    WorkRecommendation, FinancialYearLedger, MemberOfParliament,
    Society, WorkStatus, BeneficiaryCategory, ComplianceCheckLog, UserRole, Alert, User,
    ComplianceFinding
)
from rules_engine import ComplianceEngine, Severity
from db import (
    init_db, get_db, seed_sample_data, log_compliance_check, update_ledger_on_sanction,
    raise_alerts_for_work, scope_alerts_query, sync_real_mps,
    seed_compliance_controls, raise_findings_for_work, scope_findings_query,
)
from integrations import NGODarpanService, GISBoundaryService, PFMSIntegrationService
from auth import (
    CurrentUser, authenticate_user, create_access_token, get_current_user,
    require_role, scope_works_query, seed_demo_users,
    create_invited_user, reissue_invite, accept_invite, set_user_active,
)

app = FastAPI(title="MPLADS Compliance & Review API", version="2.0.0")

# Initialize database tables on startup
@app.on_event("startup")
def startup_event():
    init_db()
    db = next(get_db())
    seed_sample_data(db)
    seed_demo_users(db)
    # Guard on count so this only scans the CSVs once, not on every
    # restart -- sync_real_mps itself also skips names it's already
    # inserted, but the count check avoids paying for 930 no-op queries
    # every time the server starts once the roster is populated.
    if db.query(MemberOfParliament).count() <= 1:
        sync_real_mps(db)
    seed_compliance_controls(db)

engine = ComplianceEngine()
darpan_service = NGODarpanService()
gis_service = GISBoundaryService()
pfms_service = PFMSIntegrationService()


# --- Request Schemas ---

class WorkCreatePayload(BaseModel):
    mp_id: int
    financial_year: str = "2025-26"
    title: str
    description: str
    estimated_cost: float
    beneficiary_category: str = "general"
    is_repair_or_renovation: bool = False
    is_out_of_constituency: bool = False
    is_calamity_relief: bool = False
    work_location_district: str
    work_location_state: str
    recommendation_date: date
    darpan_id: Optional[str] = None
    written_justification: Optional[str] = None


class ReviewDecisionPayload(BaseModel):
    approved: bool
    reviewer_notes: str


class FindingAssignPayload(BaseModel):
    assigned_officer: str


class FindingResolvePayload(BaseModel):
    remediation_notes: str


class LoginPayload(BaseModel):
    email: str
    password: str


class CreateUserPayload(BaseModel):
    email: str
    full_name: str
    role: str  # "mp" | "state_nodal" | "district" | "ministry"
    scope_id: Optional[str] = None  # mp_id for MP, state/district name otherwise; null for ministry


class AcceptInvitePayload(BaseModel):
    token: str
    new_password: str


# --- Auth Endpoints ---

@app.post("/auth/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    """
    Issues a JWT for one of the 4 SIH26102 personas (MP, State Nodal
    Authority, District Authority, Ministry). Demo accounts are seeded
    on startup — see auth.seed_demo_users.
    """
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "role": user.role.value,
        "scope_id": user.scope_id,
        "full_name": user.full_name,
        "email": user.email,
    }


@app.get("/auth/me")
def get_me(current_user: CurrentUser = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "role": current_user.role.value,
        "scope_id": current_user.scope_id,
    }


@app.post("/auth/accept-invite")
def accept_invite_endpoint(payload: AcceptInvitePayload, db: Session = Depends(get_db)):
    """
    First-login password set. The invitee holds a token from a link a
    Ministry admin shared with them (POST /admin/users response) and
    picks their own password here -- Ministry never chooses or sees it.
    """
    user = accept_invite(db, payload.token, payload.new_password)
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "role": user.role.value,
        "scope_id": user.scope_id,
        "full_name": user.full_name,
        "email": user.email,
    }


# --- Admin: user provisioning (Ministry only) ---

@app.post("/admin/users")
def admin_create_user(
    payload: CreateUserPayload,
    db: Session = Depends(get_db),
    _admin: CurrentUser = Depends(require_role(UserRole.MINISTRY)),
):
    """
    Provisions an account with no password and returns an invite link.
    In production this link would be emailed to the invitee; for this
    prototype it's returned directly so the admin can share it manually.
    """
    try:
        role_enum = UserRole(payload.role)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Unknown role '{payload.role}'")

    if role_enum == UserRole.MP:
        if not payload.scope_id or not db.query(MemberOfParliament).filter(
            MemberOfParliament.id == int(payload.scope_id)
        ).first():
            raise HTTPException(status_code=422, detail="scope_id must be a real mp_id for the MP role")
    elif role_enum == UserRole.MINISTRY:
        payload.scope_id = None
    elif not payload.scope_id:
        raise HTTPException(status_code=422, detail=f"scope_id (a state/district name) is required for role '{payload.role}'")

    user = create_invited_user(db, payload.email, payload.full_name, role_enum, payload.scope_id)
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role.value,
        "scope_id": user.scope_id,
        "invite_token": user.invite_token,
        "invite_url": f"/accept-invite?token={user.invite_token}",
        "invite_expires_at": user.invite_expires_at.isoformat(),
    }


@app.post("/admin/users/{user_id}/reinvite")
def admin_reinvite_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: CurrentUser = Depends(require_role(UserRole.MINISTRY)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.password_hash:
        raise HTTPException(status_code=409, detail="This account has already accepted its invite")
    user = reissue_invite(db, user)
    return {
        "id": user.id,
        "invite_token": user.invite_token,
        "invite_url": f"/accept-invite?token={user.invite_token}",
        "invite_expires_at": user.invite_expires_at.isoformat(),
    }


def _user_status(u: User) -> str:
    if not u.password_hash:
        return "invited"
    return "active" if u.is_active else "disabled"


@app.get("/admin/users")
def admin_list_users(
    db: Session = Depends(get_db),
    _admin: CurrentUser = Depends(require_role(UserRole.MINISTRY)),
):
    users = db.query(User).order_by(User.id.desc()).all()
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role.value,
                "scope_id": u.scope_id,
                "status": _user_status(u),
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    }


@app.post("/admin/users/{user_id}/toggle-active")
def admin_toggle_active(
    user_id: int,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_role(UserRole.MINISTRY)),
):
    """Enable/disable a user's login access. Enforced immediately (see auth.get_current_user)."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.password_hash:
        raise HTTPException(status_code=409, detail="This account hasn't accepted its invite yet")

    user = set_user_active(db, user, not user.is_active)
    return {"id": user.id, "status": _user_status(user)}


@app.get("/admin/mps")
def admin_list_mps(
    db: Session = Depends(get_db),
    _admin: CurrentUser = Depends(require_role(UserRole.MINISTRY)),
):
    """Populates the MP picker on the admin 'create account' form."""
    mps = db.query(MemberOfParliament).order_by(MemberOfParliament.name).all()
    return {"mps": [{"id": mp.id, "name": mp.name, "constituency_name": mp.constituency_name, "state": mp.state} for mp in mps]}


# --- Endpoints ---

@app.post("/check-and-submit-work")
def check_and_submit_work(
    payload: WorkCreatePayload,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(UserRole.MP, UserRole.MINISTRY)),
):
    """
    Submits a new work recommendation, performs full compliance evaluation,
    saves the work & audit logs to DB, and returns the verdict.
    """
    if current_user.role == UserRole.MP and str(payload.mp_id) != str(current_user.scope_id):
        raise HTTPException(status_code=403, detail="MPs may only submit works under their own mp_id")

    mp = db.query(MemberOfParliament).filter(MemberOfParliament.id == payload.mp_id).first()
    if not mp:
        raise HTTPException(status_code=404, detail="MP not found")

    ledger = db.query(FinancialYearLedger).filter(
        FinancialYearLedger.mp_id == payload.mp_id,
        FinancialYearLedger.financial_year == payload.financial_year
    ).first()

    if not ledger:
        raise HTTPException(status_code=404, detail="Financial Year Ledger not found")

    # Wire NGO Darpan Integration if society work
    society_obj = None
    darpan_verification = None
    if payload.darpan_id:
        ngo_info = darpan_service.verify_ngo(payload.darpan_id)
        darpan_verification = ngo_info
        if ngo_info.get("valid"):
            society_obj = Society(
                name=ngo_info.get("name", "Unknown NGO"),
                darpan_id=payload.darpan_id,
                active_since=date(2020, 1, 1),
                lifetime_sanctioned_total=0.0
            )
        else:
            society_obj = Society(
                name="Unverified / Invalid NGO",
                darpan_id=None,
                active_since=date.today(),
                lifetime_sanctioned_total=0.0
            )

    cat_enum = BeneficiaryCategory.GENERAL
    if payload.beneficiary_category.lower() == "sc":
        cat_enum = BeneficiaryCategory.SC
    elif payload.beneficiary_category.lower() == "st":
        cat_enum = BeneficiaryCategory.ST

    work = WorkRecommendation(
        mp_id=payload.mp_id,
        fy_ledger_id=ledger.id,
        title=payload.title,
        description=payload.description,
        estimated_cost=payload.estimated_cost,
        beneficiary_category=cat_enum,
        is_repair_or_renovation=payload.is_repair_or_renovation,
        is_out_of_constituency=payload.is_out_of_constituency,
        is_calamity_relief=payload.is_calamity_relief,
        work_location_district=payload.work_location_district,
        work_location_state=payload.work_location_state,
        recommendation_date=payload.recommendation_date,
        status=WorkStatus.RECOMMENDED
    )

    db.add(work)
    db.commit()
    db.refresh(work)

    # Allowed districts via GIS Boundary service. Falls back to the
    # constituency's own name (not the district under test) so an
    # unmapped constituency doesn't trivially pass the jurisdiction check.
    allowed_districts = gis_service._constituency_map.get(
        mp.constituency_name, [mp.constituency_name]
    )

    context = {
        "mp_type": mp.mp_type.value,
        "mp_id": mp.id,
        "allowed_districts": allowed_districts,
        "is_calamity_declared": payload.is_calamity_relief,
        "society": society_obj,
        "raw_darpan_id": payload.darpan_id,
        "darpan_verification": darpan_verification,
        "years_active": 5 if (society_obj and society_obj.darpan_id) else 0,
        "written_justification": payload.written_justification,
    }

    report = engine.evaluate(work, ledger, context)

    # Log audit results
    log_compliance_check(db, work.id, report.results)

    # Raise risk-based alerts for BLOCK-severity failures (Epic 2)
    raise_alerts_for_work(db, work, report.results)

    # Open trackable compliance findings for the same failures (Epic 5)
    raise_findings_for_work(db, work, report.results)

    # Automatically update work status based on verdict
    if report.overall_status == "APPROVED":
        work.status = WorkStatus.SANCTIONED
        work.sanction_date = date.today()
        update_ledger_on_sanction(db, ledger.id, work)
    elif report.overall_status == "BLOCKED":
        work.status = WorkStatus.REJECTED
    elif report.overall_status == "NEEDS_REVIEW":
        work.status = WorkStatus.RECOMMENDED

    db.commit()

    return {
        "work_id": work.id,
        "overall_status": report.overall_status,
        "work_status": work.status.value,
        "results": [
            {
                "rule_id": r.rule_id,
                "para_reference": r.para_reference,
                "passed": r.passed,
                "severity": r.severity.value,
                "message": r.message,
            }
            for r in report.results
        ]
    }


@app.get("/review-queue")
def get_review_queue(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Fetch all recommended works that are pending human review (NEEDS_REVIEW), scoped to the caller's role."""
    query = db.query(WorkRecommendation).filter(
        WorkRecommendation.status == WorkStatus.RECOMMENDED
    )
    pending_works = scope_works_query(query, current_user).all()

    queue = []
    for w in pending_works:
        logs = db.query(ComplianceCheckLog).filter(
            ComplianceCheckLog.work_id == w.id,
            ComplianceCheckLog.passed == False
        ).all()
        queue.append({
            "work_id": w.id,
            "title": w.title,
            "description": w.description,
            "estimated_cost": w.estimated_cost,
            "district": w.work_location_district,
            "flagged_rules": [
                {
                    "rule_id": l.rule_id,
                    "para_reference": l.para_reference,
                    "severity": l.severity,
                    "message": l.message
                }
                for l in logs
            ]
        })
    return {"pending_reviews_count": len(queue), "queue": queue}


@app.post("/review-queue/{work_id}/decide")
def decide_review_work(
    work_id: int,
    decision: ReviewDecisionPayload,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(
        require_role(UserRole.STATE_NODAL, UserRole.DISTRICT, UserRole.MINISTRY)
    ),
):
    """
    Human reviewer endpoint to approve or reject a flagged work with notes.
    MPs are excluded — a recommending MP cannot also be the reviewer of
    their own submission (conflict of interest).
    """
    query = db.query(WorkRecommendation).filter(WorkRecommendation.id == work_id)
    work = scope_works_query(query, current_user).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found or outside your jurisdiction")

    if decision.approved:
        work.status = WorkStatus.SANCTIONED
        work.sanction_date = date.today()
        update_ledger_on_sanction(db, work.fy_ledger_id, work)
        action_msg = "Manually Approved by Human Reviewer: " + decision.reviewer_notes
    else:
        work.status = WorkStatus.REJECTED
        action_msg = "Manually Rejected by Human Reviewer: " + decision.reviewer_notes

    # Add audit entry
    log_entry = ComplianceCheckLog(
        work_id=work.id,
        rule_id="HUMAN_REVIEW_DECISION",
        para_reference="Workflow",
        passed=decision.approved,
        severity="REVIEW",
        message=action_msg,
        checked_at=date.today()
    )
    db.add(log_entry)
    db.commit()

    return {"work_id": work.id, "new_status": work.status.value, "notes": decision.reviewer_notes}


@app.get("/works")
def get_all_evaluated_works(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Fetch all evaluated works with their compliance audit check logs, scoped to the caller's role."""
    query = db.query(WorkRecommendation).order_by(WorkRecommendation.id.desc())
    works = scope_works_query(query, current_user).all()
    results = []
    for w in works:
        mp = db.query(MemberOfParliament).filter(MemberOfParliament.id == w.mp_id).first()
        logs = db.query(ComplianceCheckLog).filter(ComplianceCheckLog.work_id == w.id).all()
        
        # Calculate verdict
        has_block = any(not l.passed and l.severity == "BLOCK" for l in logs)
        has_review = any(not l.passed and l.severity == "REVIEW" for l in logs)
        verdict = "BLOCKED" if has_block else ("NEEDS_REVIEW" if has_review else "APPROVED")
        
        results.append({
            "work_id": w.id,
            "title": w.title,
            "description": w.description,
            "estimated_cost": w.estimated_cost,
            "district": w.work_location_district,
            "state": w.work_location_state,
            "mp_name": mp.name if mp else "Gorakhpur Representative MP",
            "status": w.status.value,
            "overall_status": verdict,
            "recommendation_date": w.recommendation_date.isoformat() if w.recommendation_date else None,
            "rule_checks": [
                {
                    "rule_id": l.rule_id,
                    "para_reference": l.para_reference,
                    "passed": l.passed,
                    "severity": l.severity,
                    "message": l.message
                }
                for l in logs
            ]
        })
    return {"works_count": len(results), "works": results}




# --- Features Catalog & Works Endpoints ---

# --- Compliance 1.0 Real Dataset Audit Endpoints ---
@app.get("/api/v1/features/works")
def get_v1_features_works(
    parliament: str = "all",
    search: Optional[str] = None,
    state: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    try:
        import sys
        import pandas as pd
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent / "backend"))
        from backend.compliance_engine import load_work_features, parse_num

        df = load_work_features(parliament=parliament)
        if df.empty:
            return {"total": 0, "works": []}

        if search:
            q = search.lower()
            mask = (
                df["canonical_work_id"].astype(str).str.lower().str.contains(q, na=False) |
                df["work_description"].astype(str).str.lower().str.contains(q, na=False) |
                df["mp_name"].astype(str).str.lower().str.contains(q, na=False) |
                df["state"].astype(str).str.lower().str.contains(q, na=False)
            )
            df = df[mask]

        if state and state.upper() != "ALL":
            df = df[df["state"].astype(str).str.lower() == state.lower()]

        if status and status.upper() != "ALL":
            df = df[df["lifecycle_status"].astype(str).str.upper() == status.upper()]

        total = len(df)
        paged_df = df.iloc[offset : offset + limit]

        works = []
        for idx, row in paged_df.iterrows():
            w_id = str(row.get("canonical_work_id", f"WORK-{idx}"))
            w_desc = str(row.get("work_description", "--"))
            w_state = str(row.get("state", "India")).strip()
            w_dist = str(row.get("constituency", "--")).strip()
            w_mp = str(row.get("mp_name", "--")).strip()
            sanc = parse_num(row.get("sanctioned_amount"), 0.0)
            exp = parse_num(row.get("expenditure_amount"), 0.0)
            st = str(row.get("lifecycle_status", "UNKNOWN")).upper()

            works.append({
                "work_id": w_id,
                "description": w_desc,
                "state": w_state,
                "constituency": w_dist,
                "mp_name": w_mp,
                "sanctioned_amount": sanc,
                "expenditure_amount": exp,
                "status": st,
            })

        return {"total": total, "works": works}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/compliance/summary")
def get_v1_compliance_summary(parliament: str = "all", financial_year: str = "all"):
    try:
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent / "backend"))
        from backend.compliance_engine import get_compliance_summary
        return get_compliance_summary(parliament=parliament, financial_year=financial_year)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/compliance/violations")
def get_v1_compliance_violations(
    parliament: str = "all",
    financial_year: str = "all",
    severity: Optional[str] = None,
    rule_code: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 100
):
    try:
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent / "backend"))
        from backend.compliance_engine import evaluate_compliance_violations, sample_violations_fairly
        violations = evaluate_compliance_violations(parliament=parliament, financial_year=financial_year)

        if severity and severity.upper() != "ALL":
            violations = [v for v in violations if v["severity"].upper() == severity.upper()]

        if rule_code and rule_code.upper() != "ALL":
            violations = [v for v in violations if v["rule_code"].upper() == rule_code.upper()]

        if state and state.upper() != "ALL":
            violations = [v for v in violations if v["state"].lower() == state.lower()]

        return {
            "total": len(violations),
            "violations": sample_violations_fairly(violations, limit)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# --- Compliance Alert System Endpoints ---

class FeedbackPayload(BaseModel):
    action: str
    reviewer_notes: Optional[str] = ""

@app.get("/api/v1/compliance/alerts")
def get_v1_compliance_alerts(parliament: str = "all", financial_year: str = "all", mp_name: Optional[str] = None, limit: int = 50):
    try:
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent / "backend"))
        from backend.alert_engine import get_compliance_alerts
        return get_compliance_alerts(parliament=parliament, financial_year=financial_year, mp_name=mp_name, limit=limit)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class MPNotifyPayload(BaseModel):
    alert_id: str
    mp_name: str
    channel: Optional[str] = "ALL"

@app.post("/api/v1/compliance/alerts/notify-mp")
def post_v1_notify_mp(payload: MPNotifyPayload):
    try:
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent / "backend"))
        from backend.alert_engine import dispatch_mp_alert
        return dispatch_mp_alert(alert_id=payload.alert_id, mp_name=payload.mp_name, channel=payload.channel or "ALL")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# --- Alerts (Epic 2: risk-based alerting) ---

@app.get("/alerts")
def get_alerts(
    unresolved_only: bool = True,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Alerts scoped to the caller's role/scope. A BLOCK/CRITICAL rule
    failure raises one alert per relevant persona (the work's MP, its
    state's Nodal Authority, its District Authority, and Ministry) at
    submission time -- see db.raise_alerts_for_work.
    """
    query = db.query(Alert).order_by(Alert.created_at.desc(), Alert.id.desc())
    if unresolved_only:
        query = query.filter(Alert.resolved_at.is_(None))
    alerts = scope_alerts_query(query, current_user).all()
    return {
        "unread_count": sum(1 for a in alerts if a.read_at is None),
        "alerts": [
            {
                "id": a.id,
                "work_id": a.work_id,
                "rule_code": a.rule_code,
                "severity": a.severity,
                "message": a.message,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "read_at": a.read_at.isoformat() if a.read_at else None,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
            }
            for a in alerts
        ],
    }


@app.post("/alerts/{alert_id}/read")
def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    query = db.query(Alert).filter(Alert.id == alert_id)
    alert = scope_alerts_query(query, current_user).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found or outside your jurisdiction")
    if alert.read_at is None:
        alert.read_at = date.today()
        db.commit()
    return {"id": alert.id, "read_at": alert.read_at.isoformat()}


@app.post("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(
        require_role(UserRole.STATE_NODAL, UserRole.DISTRICT, UserRole.MINISTRY)
    ),
):
    query = db.query(Alert).filter(Alert.id == alert_id)
    alert = scope_alerts_query(query, current_user).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found or outside your jurisdiction")
    alert.resolved_at = date.today()
    if alert.read_at is None:
        alert.read_at = date.today()
    db.commit()
    return {"id": alert.id, "resolved_at": alert.resolved_at.isoformat()}


# --- Compliance Action-Loop (Epic 5: flag -> assign -> resolve) ---

@app.get("/findings")
def get_findings(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Trackable compliance findings scoped to the caller's role/scope --
    see db.raise_findings_for_work (opened automatically on a BLOCK-
    severity rule failure) and db.scope_findings_query.
    """
    query = db.query(ComplianceFinding).order_by(ComplianceFinding.detected_at.desc())
    if status and status.upper() != "ALL":
        query = query.filter(ComplianceFinding.status == status.upper())
    findings = scope_findings_query(query, current_user).all()
    return {
        "findings": [
            {
                "id": f.id,
                "work_id": f.work_id,
                "control_id": f.control_id,
                "problem_summary": f.problem_summary,
                "severity": f.severity,
                "status": f.status,
                "assigned_officer": f.assigned_officer,
                "required_action": f.required_action,
                "deadline_date": f.deadline_date.isoformat() if f.deadline_date else None,
                "detected_at": f.detected_at.isoformat() if f.detected_at else None,
                "resolved_at": f.resolved_at.isoformat() if f.resolved_at else None,
                "remediation_notes": f.remediation_notes,
            }
            for f in findings
        ]
    }


@app.post("/findings/{finding_id}/assign")
def assign_finding(
    finding_id: str,
    payload: FindingAssignPayload,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(
        require_role(UserRole.STATE_NODAL, UserRole.DISTRICT, UserRole.MINISTRY)
    ),
):
    query = db.query(ComplianceFinding).filter(ComplianceFinding.id == finding_id)
    finding = scope_findings_query(query, current_user).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found or outside your jurisdiction")
    if finding.status == "RESOLVED":
        raise HTTPException(status_code=409, detail="This finding is already resolved")

    finding.assigned_officer = payload.assigned_officer
    finding.status = "IN_REMEDIATION"
    db.commit()
    return {"id": finding.id, "status": finding.status, "assigned_officer": finding.assigned_officer}


@app.post("/findings/{finding_id}/resolve")
def resolve_finding(
    finding_id: str,
    payload: FindingResolvePayload,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(
        require_role(UserRole.STATE_NODAL, UserRole.DISTRICT, UserRole.MINISTRY)
    ),
):
    query = db.query(ComplianceFinding).filter(ComplianceFinding.id == finding_id)
    finding = scope_findings_query(query, current_user).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found or outside your jurisdiction")
    if finding.status == "RESOLVED":
        raise HTTPException(status_code=409, detail="This finding is already resolved")

    finding.status = "RESOLVED"
    finding.resolved_at = date.today()
    finding.remediation_notes = payload.remediation_notes
    db.commit()
    return {"id": finding.id, "status": finding.status, "resolved_at": finding.resolved_at.isoformat()}


@app.get("/findings/resolution-rate")
def get_resolution_rate(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Real resolution-rate KPI computed from actual resolved_at timestamps
    (not fabricated -- see mdfiles/PRD_GAP_CLOSURE.md's Epic 5 acceptance
    criteria). Scoped like /findings, so a District Authority sees their
    own rate and Ministry sees the national one.
    """
    findings = scope_findings_query(db.query(ComplianceFinding), current_user).all()
    total = len(findings)
    resolved = sum(1 for f in findings if f.status == "RESOLVED")
    overdue_open = sum(
        1 for f in findings
        if f.status != "RESOLVED" and f.deadline_date and f.deadline_date < date.today()
    )
    return {
        "total_findings": total,
        "resolved_count": resolved,
        "resolution_rate": round(resolved / total, 4) if total else None,
        "open_overdue_count": overdue_open,
    }
