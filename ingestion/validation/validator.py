import os
import sys
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.app.db.models import (
    WorkRecommended, WorkSanctioned, Expenditure, WorkCompleted,
    MPMaster, VendorMaster, IDAMaster, Geography
)

class DataValidator:
    def __init__(self, db: Session, house: str = "all"):
        self.db = db
        self.house = house.lower()

    def _filter_house(self, query):
        if self.house in ["lok_sabha", "loksabha", "ls"]:
            return query.filter(WorkRecommended.house == "Lok Sabha")
        elif self.house in ["rajya_sabha", "rajyasabha", "rs"]:
            return query.filter(WorkRecommended.house == "Rajya Sabha")
        return query

    def run_all_checks(self) -> dict:
        """Executes all 5 data validation suites and returns a consolidated report."""
        type_results = self.check_types()
        null_results = self.profile_nulls()
        date_results = self.check_date_sequences()
        currency_results = self.check_currency()
        ref_results = self.check_referential_integrity()

        total_issues = (
            type_results["type_error_count"] +
            date_results["total_date_violations"] +
            currency_results["total_currency_issues"] +
            ref_results["total_orphan_count"]
        )

        overall_status = "PASSED" if total_issues == 0 else ("WARNING" if total_issues < 100 else "FAILED")

        house_label = "All Houses"
        if self.house in ["lok_sabha", "loksabha", "ls"]:
            house_label = "Lok Sabha"
        elif self.house in ["rajya_sabha", "rajyasabha", "rs"]:
            house_label = "Rajya Sabha"

        return {
            "summary": {
                "timestamp": datetime.utcnow().isoformat(),
                "house_filter": self.house,
                "house_label": house_label,
                "overall_status": overall_status,
                "total_issues_found": total_issues
            },
            "type_checks": type_results,
            "null_profiling": null_results,
            "date_sequence_checks": date_results,
            "currency_checks": currency_results,
            "referential_checks": ref_results
        }

    # 1. Type Checks
    def check_types(self) -> dict:
        errors = []
        q = self.db.query(WorkRecommended).filter(WorkRecommended.recommended_amount.is_(None))
        invalid_rec_amounts = self._filter_house(q).count()
        if invalid_rec_amounts > 0:
            errors.append(f"Found {invalid_rec_amounts} works with non-integer/null recommended_amount.")

        invalid_exp_amounts = self.db.query(Expenditure).filter(
            Expenditure.amount.is_(None)
        ).count()
        if invalid_exp_amounts > 0:
            errors.append(f"Found {invalid_exp_amounts} transactions with non-integer/null amount.")

        return {
            "status": "PASSED" if len(errors) == 0 else "WARNING",
            "type_error_count": len(errors),
            "errors": errors
        }

    # 2. Null Profiling
    def profile_nulls(self) -> dict:
        total_rec = self._filter_house(self.db.query(WorkRecommended)).count()
        total_sanc = self._filter_house(self.db.query(WorkSanctioned).join(WorkRecommended)).count()
        total_exp = self._filter_house(self.db.query(Expenditure).join(WorkRecommended)).count()

        null_rec_dates = self._filter_house(self.db.query(WorkRecommended).filter(WorkRecommended.recommendation_date.is_(None))).count()
        null_categories = self._filter_house(self.db.query(WorkRecommended).filter(WorkRecommended.category.is_(None))).count()
        null_sanc_dates = self._filter_house(self.db.query(WorkSanctioned).join(WorkRecommended).filter(WorkSanctioned.sanction_date.is_(None))).count()
        null_txn_dates = self._filter_house(self.db.query(Expenditure).join(WorkRecommended).filter(Expenditure.txn_date.is_(None))).count()

        return {
            "works_recommended": {
                "total_rows": total_rec,
                "null_recommendation_dates": null_rec_dates,
                "null_categories": null_categories,
                "completeness_pct": round((1.0 - (null_rec_dates / (total_rec or 1))) * 100, 2)
            },
            "works_sanctioned": {
                "total_rows": total_sanc,
                "null_sanction_dates": null_sanc_dates,
                "completeness_pct": round((1.0 - (null_sanc_dates / (total_sanc or 1))) * 100, 2)
            },
            "expenditure": {
                "total_rows": total_exp,
                "null_txn_dates": null_txn_dates,
                "completeness_pct": round((1.0 - (null_txn_dates / (total_exp or 1))) * 100, 2)
            }
        }

    # 3. Date Sequence Checks
    def check_date_sequences(self) -> dict:
        violations = []

        q_sanc = self.db.query(WorkSanctioned).join(
            WorkRecommended, WorkSanctioned.work_id == WorkRecommended.work_id
        ).filter(
            WorkSanctioned.sanction_date < WorkRecommended.recommendation_date
        )
        sanc_before_rec = self._filter_house(q_sanc).all()

        if sanc_before_rec:
            violations.append({
                "rule": "sanction_date_before_recommendation_date",
                "count": len(sanc_before_rec),
                "severity": "HIGH",
                "sample_work_ids": [w.work_id for w in sanc_before_rec[:5]]
            })

        q_exp = self.db.query(Expenditure).join(
            WorkRecommended, Expenditure.work_id == WorkRecommended.work_id
        ).join(
            WorkSanctioned, Expenditure.work_id == WorkSanctioned.work_id
        ).filter(
            Expenditure.txn_date < WorkSanctioned.sanction_date
        )
        exp_before_sanc = self._filter_house(q_exp).all()

        if exp_before_sanc:
            violations.append({
                "rule": "expenditure_before_sanction_date",
                "count": len(exp_before_sanc),
                "severity": "CRITICAL",
                "sample_work_ids": list(set([e.work_id for e in exp_before_sanc[:5]]))
            })

        q_comp = self.db.query(WorkCompleted).join(
            WorkRecommended, WorkCompleted.work_id == WorkRecommended.work_id
        ).join(
            WorkSanctioned, WorkCompleted.work_id == WorkSanctioned.work_id
        ).filter(
            WorkCompleted.completion_date < WorkSanctioned.sanction_date
        )
        comp_before_sanc = self._filter_house(q_comp).all()

        if comp_before_sanc:
            violations.append({
                "rule": "completion_before_sanction_date",
                "count": len(comp_before_sanc),
                "severity": "HIGH",
                "sample_work_ids": [w.work_id for w in comp_before_sanc[:5]]
            })

        now = datetime.now()
        q_fut = self.db.query(WorkRecommended).filter(WorkRecommended.recommendation_date > now)
        future_recs = self._filter_house(q_fut).count()
        if future_recs > 0:
            violations.append({
                "rule": "future_recommendation_date",
                "count": future_recs,
                "severity": "MEDIUM"
            })

        total_violations = sum(v["count"] for v in violations)

        return {
            "status": "PASSED" if total_violations == 0 else "WARNING",
            "total_date_violations": total_violations,
            "rules_violated": violations
        }

    # 4. Currency Parsing & Boundary Checks
    def check_currency(self) -> dict:
        issues = []

        q_neg_rec = self.db.query(WorkRecommended).filter(WorkRecommended.recommended_amount < 0)
        neg_rec = self._filter_house(q_neg_rec).count()
        if neg_rec > 0:
            issues.append({"rule": "negative_recommended_amount", "count": neg_rec, "severity": "HIGH"})

        q_neg_exp = self.db.query(Expenditure).join(WorkRecommended).filter(Expenditure.amount < 0)
        neg_exp = self._filter_house(q_neg_exp).count()
        if neg_exp > 0:
            issues.append({"rule": "negative_expenditure_amount", "count": neg_exp, "severity": "HIGH"})

        q_zero_rec = self.db.query(WorkRecommended).filter(WorkRecommended.recommended_amount == 0)
        zero_rec = self._filter_house(q_zero_rec).count()
        if zero_rec > 0:
            issues.append({"rule": "zero_recommended_amount", "count": zero_rec, "severity": "MEDIUM"})

        limit_paise = 5000000000
        q_exc = self.db.query(WorkRecommended).filter(WorkRecommended.recommended_amount > limit_paise)
        excessive_works = self._filter_house(q_exc).count()
        if excessive_works > 0:
            issues.append({"rule": "exceeds_single_work_policy_limit", "count": excessive_works, "severity": "HIGH"})

        total_issues = sum(i["count"] for i in issues)

        return {
            "status": "PASSED" if total_issues == 0 else "WARNING",
            "total_currency_issues": total_issues,
            "issue_details": issues
        }

    # 5. Referential Integrity Checks (Orphans)
    def check_referential_integrity(self) -> dict:
        orphans = []

        orphan_sanc = self.db.query(WorkSanctioned).outerjoin(
            WorkRecommended, WorkSanctioned.work_id == WorkRecommended.work_id
        ).filter(WorkRecommended.work_id.is_(None)).count()

        if orphan_sanc > 0:
            orphans.append({"relationship": "works_sanctioned -> works_recommended", "orphan_count": orphan_sanc})

        orphan_exp = self.db.query(Expenditure).outerjoin(
            WorkRecommended, Expenditure.work_id == WorkRecommended.work_id
        ).filter(WorkRecommended.work_id.is_(None)).count()

        if orphan_exp > 0:
            orphans.append({"relationship": "expenditure -> works_recommended", "orphan_count": orphan_exp})

        orphan_mp = self.db.query(WorkRecommended).outerjoin(
            MPMaster, WorkRecommended.mp_id == MPMaster.mp_id
        ).filter(MPMaster.mp_id.is_(None)).count()

        if orphan_mp > 0:
            orphans.append({"relationship": "works_recommended -> mp_master", "orphan_count": orphan_mp})

        orphan_vendor = self.db.query(Expenditure).outerjoin(
            VendorMaster, Expenditure.vendor_id == VendorMaster.vendor_id
        ).filter(VendorMaster.vendor_id.is_(None)).count()

        if orphan_vendor > 0:
            orphans.append({"relationship": "expenditure -> vendor_master", "orphan_count": orphan_vendor})

        total_orphans = sum(o["orphan_count"] for o in orphans)

        return {
            "status": "PASSED" if total_orphans == 0 else "WARNING",
            "total_orphan_count": total_orphans,
            "orphan_details": orphans
        }
