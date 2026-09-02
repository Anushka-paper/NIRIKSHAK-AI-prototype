import pandas as pd
from data_pipeline.compliance.config import COMPLIANCE_RULES

def evaluate_transaction_rules(df_txn):
    violations = []
    if df_txn.empty:
        return violations

    for idx, row in df_txn.iterrows():
        txn_id = str(row.get("transaction_id", f"TXN_{idx+1:08d}"))
        work_id = str(row.get("canonical_work_id", "UNKNOWN"))
        vendor_name = str(row.get("canonical_vendor_name", "UNKNOWN"))

        # R001: EXP_BEFORE_SANCTION
        days_sanc = row.get("days_since_sanction", None)
        if pd.notna(days_sanc) and float(days_sanc) < 0:
            violations.append({
                "rule_code": "R001",
                "rule_name": COMPLIANCE_RULES["R001"]["name"],
                "severity": COMPLIANCE_RULES["R001"]["severity"],
                "weight": COMPLIANCE_RULES["R001"]["weight"],
                "entity_type": "TRANSACTION",
                "entity_id": txn_id,
                "source_house": "UNKNOWN",
                "state": "UNKNOWN",
                "mp_name": "UNKNOWN",
                "description": f"Disbursement date precedes sanction date by {abs(float(days_sanc)):.0f} days",
                "action": COMPLIANCE_RULES["R001"]["action"]
            })

    # R007: EXACT_DUPLICATE_PAYMENT
    if len(df_txn) > 1 and "expenditure_amount_inr" in df_txn.columns:
        dup_cols = [c for c in ["canonical_work_id", "canonical_vendor_name", "expenditure_amount_inr", "expenditure_date"] if c in df_txn.columns]
        if len(dup_cols) >= 3:
            dups = df_txn[df_txn.duplicated(subset=dup_cols, keep=False)]
            for idx, row in dups.iterrows():
                txn_id = str(row.get("transaction_id", f"TXN_{idx+1:08d}"))
                work_id = str(row.get("canonical_work_id", "UNKNOWN"))
                amt = float(row.get("expenditure_amount_inr", 0.0) or 0.0)
                violations.append({
                    "rule_code": "R007",
                    "rule_name": COMPLIANCE_RULES["R007"]["name"],
                    "severity": COMPLIANCE_RULES["R007"]["severity"],
                    "weight": COMPLIANCE_RULES["R007"]["weight"],
                    "entity_type": "TRANSACTION",
                    "entity_id": txn_id,
                    "source_house": "UNKNOWN",
                    "state": "UNKNOWN",
                    "mp_name": "UNKNOWN",
                    "description": f"Exact duplicate payment transaction key detected for amount ₹{amt:,.2f}",
                    "action": COMPLIANCE_RULES["R007"]["action"]
                })

    return violations
