import pandas as pd
from data_pipeline.compliance.rules_work import evaluate_work_rules
from data_pipeline.compliance.rules_transaction import evaluate_transaction_rules

class ComplianceEvaluator:
    def __init__(self):
        pass

    def run_all_evaluations(self, df_work, df_lifecycle, df_txn):
        print(f"[COMPLIANCE ENGINE] Evaluating deterministic compliance rules...")
        
        work_violations = evaluate_work_rules(df_work, df_lifecycle)
        txn_violations = evaluate_transaction_rules(df_txn)
        
        all_violations = work_violations + txn_violations
        df_viol = pd.DataFrame(all_violations) if all_violations else pd.DataFrame(columns=[
            "rule_code", "rule_name", "severity", "weight", "entity_type", "entity_id",
            "source_house", "state", "mp_name", "description", "action"
        ])
        
        print(f"[COMPLIANCE ENGINE] Evaluated rules across {len(df_work):,} works. Total violations flagged: {len(df_viol):,}")
        return df_viol
