"""
Database manager and persistence helper for NIRIKSHAK AI.
Handles connection, initialization, seed data creation, transactional ledger updates,
and compliance log persistence.
"""

import csv
from datetime import date, timedelta
from pathlib import Path
from typing import List, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from models import (
    Base, MemberOfParliament, MPType, FinancialYearLedger, WorkRecommendation,
    WorkStatus, BeneficiaryCategory, ComplianceCheckLog, Alert, UserRole,
    ComplianceControl, ComplianceFinding
)

DB_URL = "sqlite:///mplads_nirikshak.db"
DATA_DIR = Path(__file__).resolve().parent / "data" / "canonical"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables in the SQLite/Postgres database."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency / generator for acquiring database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_sample_data(db: Session) -> Tuple[MemberOfParliament, FinancialYearLedger]:
    """Seed sample MP and Ledger if none exists."""
    mp = db.query(MemberOfParliament).first()
    if not mp:
        mp = MemberOfParliament(
            id=1,
            name="Gorakhpur Representative MP",
            mp_type=MPType.LOK_SABHA,
            constituency_name="Gorakhpur",
            state="Uttar Pradesh",
            term_start_date=date(2024, 6, 1),
        )
        db.add(mp)
        db.commit()
        db.refresh(mp)

    ledger = db.query(FinancialYearLedger).filter(
        FinancialYearLedger.mp_id == mp.id,
        FinancialYearLedger.financial_year == "2025-26"
    ).first()

    if not ledger:
        ledger = FinancialYearLedger(
            id=1,
            mp_id=mp.id,
            financial_year="2025-26",
            base_entitlement=50_000_000,
            tenure_multiplier=1.0,
            prorated_entitlement=50_000_000,
            cumulative_sanctioned=10_000_000,
            cumulative_disbursed=5_000_000,
            sc_area_sanctioned=2_000_000,
            st_area_sanctioned=1_000_000,
            repair_renovation_sanctioned=1_500_000,
            out_of_constituency_sanctioned=0.0,
        )
        db.add(ledger)
        db.commit()
        db.refresh(ledger)

    # Seed ongoing, completed, and recommended works if database is fresh
    if db.query(WorkRecommendation).count() == 0:
        sample_works = [
            WorkRecommendation(
                id=1,
                mp_id=mp.id,
                fy_ledger_id=ledger.id,
                title="Community Drinking Water Pipeline",
                description="Installation of public drinking water pipeline in ward 4.",
                estimated_cost=1_500_000,
                beneficiary_category=BeneficiaryCategory.GENERAL,
                work_location_district="Gorakhpur",
                work_location_state="Uttar Pradesh",
                recommendation_date=date(2024, 10, 1),
                sanction_date=date(2024, 11, 5),
                completion_deadline=date(2025, 11, 5),
                status=WorkStatus.EXECUTING  # Ongoing
            ),
            WorkRecommendation(
                id=2,
                mp_id=mp.id,
                fy_ledger_id=ledger.id,
                title="Government Primary School Solar Roof",
                description="Installation of 10kW rooftop solar power system for primary school.",
                estimated_cost=850_000,
                beneficiary_category=BeneficiaryCategory.SC,
                work_location_district="Gorakhpur",
                work_location_state="Uttar Pradesh",
                recommendation_date=date(2024, 4, 1),
                sanction_date=date(2024, 4, 25),
                completion_deadline=date(2024, 12, 31),
                actual_completion_date=date(2024, 11, 20),
                status=WorkStatus.COMPLETED  # Completed
            ),
            WorkRecommendation(
                id=3,
                mp_id=mp.id,
                fy_ledger_id=ledger.id,
                title="Public Health Centre Ambulatory Ward",
                description="Construction of emergency patient ward at Community Health Centre.",
                estimated_cost=3_200_000,
                beneficiary_category=BeneficiaryCategory.ST,
                work_location_district="Gorakhpur",
                work_location_state="Uttar Pradesh",
                recommendation_date=date(2023, 1, 15),
                sanction_date=date(2023, 3, 1),
                completion_deadline=date(2024, 3, 1),
                actual_completion_date=date(2024, 6, 15),  # Completed delayed (SLA warning)
                status=WorkStatus.COMPLETED  # Completed (with SLA warning)
            ),
            WorkRecommendation(
                id=4,
                mp_id=mp.id,
                fy_ledger_id=ledger.id,
                title="Temple Road Repair & Swagat Dwar",
                description="Repair of road near temple and construction of swagat dwar.",
                estimated_cost=2_800_000,
                is_repair_or_renovation=True,
                beneficiary_category=BeneficiaryCategory.GENERAL,
                work_location_district="Gorakhpur",
                work_location_state="Uttar Pradesh",
                recommendation_date=date(2025, 1, 10),
                status=WorkStatus.RECOMMENDED  # Flagged/Needs Review
            )
        ]
        for w in sample_works:
            db.add(w)
        db.commit()

        # Run compliance engine on seeded works and log check results
        from rules_engine import ComplianceEngine
        engine = ComplianceEngine()
        context = {
            "mp_type": mp.mp_type.value,
            "mp_id": mp.id,
            "allowed_districts": ["Gorakhpur", "Deoria"],
            "is_calamity_declared": False,
            "society": None,
        }
        for w in sample_works:
            report = engine.evaluate(w, ledger, context)
            log_compliance_check(db, w.id, report.results)

    return mp, ledger


def log_compliance_check(db: Session, work_id: int, results: list):
    """Persist compliance check results to ComplianceCheckLog audit table."""
    for r in results:
        log_entry = ComplianceCheckLog(
            work_id=work_id,
            rule_id=r.rule_id,
            para_reference=r.para_reference,
            passed=r.passed,
            severity=r.severity.value,
            message=r.message,
            checked_at=date.today()
        )
        db.add(log_entry)
    db.commit()


def update_ledger_on_sanction(db: Session, ledger_id: int, work: WorkRecommendation):
    """
    Transactionally update the FinancialYearLedger running totals
    when a work is officially sanctioned.
    """
    ledger = db.query(FinancialYearLedger).filter(FinancialYearLedger.id == ledger_id).first()
    if not ledger:
        return

    cost = work.estimated_cost

    # Use SQL-side increments (UPDATE col = col + amount) rather than a
    # Python read-modify-write, so concurrent sanctions can't silently
    # overwrite each other's totals (lost update).
    values = {"cumulative_sanctioned": FinancialYearLedger.cumulative_sanctioned + cost}
    if work.is_repair_or_renovation:
        values["repair_renovation_sanctioned"] = FinancialYearLedger.repair_renovation_sanctioned + cost
    if work.is_out_of_constituency:
        values["out_of_constituency_sanctioned"] = FinancialYearLedger.out_of_constituency_sanctioned + cost
    if work.beneficiary_category == BeneficiaryCategory.SC:
        values["sc_area_sanctioned"] = FinancialYearLedger.sc_area_sanctioned + cost
    elif work.beneficiary_category == BeneficiaryCategory.ST:
        values["st_area_sanctioned"] = FinancialYearLedger.st_area_sanctioned + cost

    db.query(FinancialYearLedger).filter(FinancialYearLedger.id == ledger_id).update(
        values, synchronize_session=False
    )
    db.commit()
    db.refresh(ledger)


# High-severity values from each engine that should raise an Alert.
# rules_engine.Severity.BLOCK.value == "BLOCK"; backend/compliance_engine.py
# uses "CRITICAL" — both funnel into the same Alert table.
ALERT_WORTHY_SEVERITIES = {"BLOCK", "CRITICAL"}


def raise_alerts_for_work(db: Session, work: WorkRecommendation, rule_results: List) -> List[Alert]:
    """
    Given the RuleResult list from ComplianceEngine.evaluate() for a work,
    create Alert rows for every high-severity failure, scoped to the
    work's MP, its state's Nodal Authority, and the Ministry rollup.
    Epic 2 of mdfiles/PRD_GAP_CLOSURE.md.
    """
    created: List[Alert] = []
    for r in rule_results:
        severity = r.severity.value if hasattr(r.severity, "value") else str(r.severity)
        if r.passed or severity not in ALERT_WORTHY_SEVERITIES:
            continue

        targets = [
            (UserRole.MP, str(work.mp_id)),
            (UserRole.STATE_NODAL, work.work_location_state),
            (UserRole.DISTRICT, work.work_location_district),
            (UserRole.MINISTRY, None),
        ]
        for target_role, target_scope_id in targets:
            alert = Alert(
                work_id=work.id,
                rule_code=r.rule_id,
                severity=severity,
                message=r.message,
                target_role=target_role,
                target_scope_id=target_scope_id,
                created_at=date.today(),
            )
            db.add(alert)
            created.append(alert)

    if created:
        db.commit()
    return created


def scope_alerts_query(query, current_user):
    """Mirror of auth.scope_works_query, but over Alert.target_role/target_scope_id."""
    if current_user.role == UserRole.MINISTRY:
        return query
    return query.filter(
        Alert.target_role == current_user.role,
        Alert.target_scope_id == current_user.scope_id,
    )



def sync_real_mps(db: Session) -> int:
    """
    Populates MemberOfParliament from the real scraped MPLADS roster
    (data/canonical/{lok_sabha,rajya_sabha}/mps.csv + constituencies.csv)
    instead of leaving only the single fictional demo MP seeded by
    seed_sample_data. Needed so admin tooling (the /admin/users MP
    picker) can provision an account for any of the ~930 real MPs, not
    just the one demo record.

    Idempotent via a row-count guard in the caller (see api.py startup)
    -- this function itself just inserts once per call, so don't call
    it unconditionally on every startup once the table is populated.
    The seeded demo MP (id=1) is left untouched since existing demo
    WorkRecommendation/Alert rows reference it by id.
    """
    inserted = 0
    for parliament, mp_type in [
        ("lok_sabha", MPType.LOK_SABHA),
        ("rajya_sabha", MPType.RAJYA_SABHA_ELECTED),
    ]:
        mps_path = DATA_DIR / parliament / "mps.csv"
        constituencies_path = DATA_DIR / parliament / "constituencies.csv"
        if not mps_path.exists():
            continue

        constituency_by_mp_id = {}
        if constituencies_path.exists():
            with open(constituencies_path, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    constituency_by_mp_id[row["mp_id"]] = row["name"]

        term_start = date(2024, 6, 1) if parliament == "lok_sabha" else date(2020, 4, 1)

        with open(mps_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = row["name"].strip()
                state = row["state"].strip()
                if not name:
                    continue
                exists = db.query(MemberOfParliament).filter(
                    MemberOfParliament.name == name,
                    MemberOfParliament.state == state,
                ).first()
                if exists:
                    continue
                db.add(MemberOfParliament(
                    name=name,
                    mp_type=mp_type,
                    constituency_name=constituency_by_mp_id.get(row["mp_id"]),
                    state=state,
                    term_start_date=term_start,
                ))
                inserted += 1

    if inserted:
        db.commit()
    return inserted


# ---------------------------------------------------------------------
# Epic 5: Compliance Action-Loop (flag -> assign -> resolve)
# ---------------------------------------------------------------------

# Findings are only auto-raised for failures at this severity -- mirrors
# ALERT_WORTHY_SEVERITIES in spirit, but findings are a heavier, tracked
# workflow object (assignment + deadline + resolution), so we reserve
# them for the highest-severity statutory rule (BLOCK), not every WARN.
FINDING_WORTHY_SEVERITIES = {"BLOCK"}
FINDING_REMEDIATION_DAYS = 30


def seed_compliance_controls(db: Session) -> None:
    """
    Populates ComplianceControl from rules_engine.DEFAULT_RULES so every
    ComplianceFinding has a real control to reference, instead of
    inventing a separate, disconnected "C001-C010" numbering scheme.
    """
    if db.query(ComplianceControl).count() > 0:
        return

    from rules_engine import DEFAULT_RULES

    for rule in DEFAULT_RULES:
        category = rule.rule_id.split("_")[0]  # FIN / GEO / NEG / SOC / SLA
        category_map = {
            "FIN": "Financial", "GEO": "Technical", "NEG": "Documentation",
            "SOC": "Administrative", "SLA": "Physical",
        }
        db.add(ComplianceControl(
            id=rule.rule_id,
            name=type(rule).__name__,
            para_reference=rule.para_reference,
            category=category_map.get(category, "Administrative"),
            description=f"Statutory check enforced by {type(rule).__name__} ({rule.para_reference}).",
            severity=rule.severity.value,
            frequency="Continuous",
        ))
    db.commit()


def raise_findings_for_work(db: Session, work: WorkRecommendation, rule_results: List) -> List[ComplianceFinding]:
    """
    Creates a trackable ComplianceFinding for every BLOCK-severity rule
    failure -- the "flag" half of "flag -> assign -> resolve". Assigns
    to the work's district by default (District Authority is the usual
    first responder per the review-queue convention already used
    elsewhere in this codebase); Ministry/State Nodal can reassign via
    POST /findings/{id}/assign.
    """
    created: List[ComplianceFinding] = []
    for r in rule_results:
        severity = r.severity.value if hasattr(r.severity, "value") else str(r.severity)
        if r.passed or severity not in FINDING_WORTHY_SEVERITIES:
            continue

        finding_id = f"MPL-{work.id}-{r.rule_id}"
        if db.query(ComplianceFinding).filter(ComplianceFinding.id == finding_id).first():
            continue  # already raised for this work+rule (e.g. re-check)

        today = date.today()
        finding = ComplianceFinding(
            id=finding_id,
            work_id=work.id,
            control_id=r.rule_id,
            problem_summary=r.message,
            severity=severity,
            status="OPEN",
            assigned_officer=f"{work.work_location_district} District Authority",
            required_action=f"Review and resolve statutory violation under {r.para_reference}.",
            deadline_date=today + timedelta(days=FINDING_REMEDIATION_DAYS),
            detected_at=today,
        )
        db.add(finding)
        created.append(finding)

    if created:
        db.commit()
    return created


def scope_findings_query(query, current_user):
    """
    Same role/scope rules as scope_works_query, joined through
    ComplianceFinding.work_id -> WorkRecommendation, since a finding has
    no jurisdiction fields of its own.
    """
    if current_user.role == UserRole.MINISTRY:
        return query
    query = query.join(WorkRecommendation, ComplianceFinding.work_id == WorkRecommendation.id)
    if current_user.role == UserRole.MP:
        return query.filter(WorkRecommendation.mp_id == int(current_user.scope_id))
    if current_user.role == UserRole.STATE_NODAL:
        return query.filter(WorkRecommendation.work_location_state == current_user.scope_id)
    if current_user.role == UserRole.DISTRICT:
        return query.filter(WorkRecommendation.work_location_district == current_user.scope_id)
    return query.filter(False)
