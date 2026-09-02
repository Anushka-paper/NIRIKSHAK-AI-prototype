import os
import json
import pandas as pd
from data_pipeline.features.work_features import compute_work_features
from data_pipeline.features.transaction_features import compute_transaction_features
from data_pipeline.features.vendor_features import compute_vendor_features
from data_pipeline.features.mp_features import compute_mp_features
from data_pipeline.features.dictionary_generator import generate_feature_dictionary_files

def run_feature_engineering_pipeline():
    print("=========================================================================")
    print("      STARTING CANONICAL FEATURE STORE GENERATION (v1.0)")
    print("=========================================================================")
    
    # Load Master & Lifecycle Datasets
    master_path = os.path.join("data", "integrated", "master", "unified_work_lifecycle.csv")
    df_lifecycle = pd.read_csv(master_path, low_memory=False) if os.path.exists(master_path) else pd.DataFrame()
    
    ls_exp_path = os.path.join("data", "standardised", "lok_sabha", "std_expenditure.csv")
    rs_exp_path = os.path.join("data", "standardised", "rajya_sabha", "std_expenditure.csv")
    df_ls_exp = pd.read_csv(ls_exp_path, low_memory=False) if os.path.exists(ls_exp_path) else pd.DataFrame()
    df_rs_exp = pd.read_csv(rs_exp_path, low_memory=False) if os.path.exists(rs_exp_path) else pd.DataFrame()
    df_exp = pd.concat([df_ls_exp, df_rs_exp], ignore_index=True)
    
    vendor_master_path = os.path.join("data", "entity_resolution", "master", "vendor_master.csv")
    df_vendor_master = pd.read_csv(vendor_master_path, low_memory=False) if os.path.exists(vendor_master_path) else pd.DataFrame()
    
    mp_master_path = os.path.join("data", "entity_resolution", "master", "mp_master.csv")
    df_mp_master = pd.read_csv(mp_master_path, low_memory=False) if os.path.exists(mp_master_path) else pd.DataFrame()
    
    # Compute 4 Canonical Feature Tables
    feats_work = compute_work_features(df_lifecycle)
    feats_txn = compute_transaction_features(df_exp, df_lifecycle)
    feats_vendor = compute_vendor_features(df_vendor_master, df_exp, df_lifecycle)
    feats_mp = compute_mp_features(df_mp_master, df_lifecycle, pd.DataFrame())
    
    # Save CSV Outputs to data/features/
    feat_dir = os.path.join("data", "features")
    os.makedirs(feat_dir, exist_ok=True)
    
    feats_work.to_csv(os.path.join(feat_dir, "features_work.csv"), index=False, encoding="utf-8")
    feats_txn.to_csv(os.path.join(feat_dir, "features_transaction.csv"), index=False, encoding="utf-8")
    feats_vendor.to_csv(os.path.join(feat_dir, "features_vendor.csv"), index=False, encoding="utf-8")
    feats_mp.to_csv(os.path.join(feat_dir, "features_mp.csv"), index=False, encoding="utf-8")
    
    # Generate Feature Dictionaries
    generate_feature_dictionary_files(feat_dir)
    
    # Generate Quality Summary Report
    rep_dir = os.path.join("data", "reports")
    os.makedirs(rep_dir, exist_ok=True)
    rep_data = {
        "status": "SUCCESS",
        "feature_version": "v1.0",
        "canonical_tables": {
            "features_work": len(feats_work),
            "features_transaction": len(feats_txn),
            "features_vendor": len(feats_vendor),
            "features_mp": len(feats_mp)
        }
    }
    with open(os.path.join(rep_dir, "feature_store_report.json"), "w", encoding="utf-8") as f:
        json.dump(rep_data, f, indent=2)
        
    print("[NIRIKSHAK AI] Canonical Feature Store pipeline completed successfully!")

if __name__ == "__main__":
    run_feature_engineering_pipeline()
