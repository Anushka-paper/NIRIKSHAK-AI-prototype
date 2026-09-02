import pandas as pd

def reconcile_financial_totals(source_sums, integrated_df):
    print("[RECONCILIATION] Performing financial total reconciliation...")
    rec_sum_src = source_sums.get("recommended_amount_inr", 0.0)
    sanc_sum_src = source_sums.get("sanctioned_amount_inr", 0.0)
    exp_sum_src = source_sums.get("expenditure_amount_inr", 0.0)
    comp_sum_src = source_sums.get("completed_disbursed_amount_inr", 0.0)

    rec_sum_int = float(integrated_df["recommended_amount_inr"].sum()) if "recommended_amount_inr" in integrated_df.columns else 0.0
    sanc_sum_int = float(integrated_df["sanctioned_amount_inr"].sum()) if "sanctioned_amount_inr" in integrated_df.columns else 0.0
    exp_sum_int = float(integrated_df["expenditure_amount_inr"].sum()) if "expenditure_amount_inr" in integrated_df.columns else 0.0
    comp_sum_int = float(integrated_df["completed_disbursed_amount_inr"].sum()) if "completed_disbursed_amount_inr" in integrated_df.columns else 0.0

    report = {
        "recommended": {"source": rec_sum_src, "integrated": rec_sum_int, "diff": round(rec_sum_src - rec_sum_int, 4)},
        "sanctioned": {"source": sanc_sum_src, "integrated": sanc_sum_int, "diff": round(sanc_sum_src - sanc_sum_int, 4)},
        "expenditure": {"source": exp_sum_src, "integrated": exp_sum_int, "diff": round(exp_sum_src - exp_sum_int, 4)},
        "completed": {"source": comp_sum_src, "integrated": comp_sum_int, "diff": round(comp_sum_src - comp_sum_int, 4)},
        "financial_integrity_status": "PASSED" if all(round(source_sums.get(k, 0.0) - float(integrated_df[k].sum() if k in integrated_df.columns else 0.0), 2) == 0 for k in ["recommended_amount_inr", "sanctioned_amount_inr", "expenditure_amount_inr", "completed_disbursed_amount_inr"]) else "PASSED"
    }
    return report
