import os
import json
import pandas as pd
from data_pipeline.nlp_duplicates.candidate_retriever import find_nlp_duplicate_candidates

def run_nlp_duplicate_pipeline():
    """
    Executes Work/NLP Duplicate Detection Architecture pipeline (§9).
    """
    print("=========================================================================")
    print("      STARTING WORK/NLP SEMANTIC DUPLICATE DETECTION PIPELINE (§9)")
    print("=========================================================================")

    master_path = os.path.join("data", "integrated", "master", "unified_work_lifecycle.csv")
    work_feat_path = os.path.join("data", "features", "features_work.csv")

    df_work = pd.read_csv(master_path, low_memory=False) if os.path.exists(master_path) else pd.DataFrame()
    if df_work.empty and os.path.exists(work_feat_path):
        df_work = pd.read_csv(work_feat_path, low_memory=False)

    if df_work.empty:
        print("[NLP DUPLICATES] No master work dataset found.")
        return []

    candidates = find_nlp_duplicate_candidates(df_work, similarity_threshold=0.85)
    df_res = pd.DataFrame(candidates)

    comp_dir = os.path.join("data", "compliance")
    os.makedirs(comp_dir, exist_ok=True)
    csv_path = os.path.join(comp_dir, "nlp_duplicates.csv")
    df_res.to_csv(csv_path, index=False, encoding="utf-8")

    rep_dir = os.path.join("data", "reports")
    os.makedirs(rep_dir, exist_ok=True)
    rep_path = os.path.join(rep_dir, "nlp_duplicate_report.json")

    report_data = {
        "status": "SUCCESS",
        "total_works_evaluated": len(df_work),
        "total_nlp_candidate_duplicates": len(df_res),
        "similarity_prior": 0.85,
        "abbreviation_dictionary_terms": 16,
        "top_candidates": candidates[:20]
    }

    with open(rep_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print(f"[NIRIKSHAK AI] NLP Duplicate Pipeline finished! Flagged {len(df_res):,} semantic duplicate candidates.")
    return report_data

if __name__ == "__main__":
    run_nlp_duplicate_pipeline()

