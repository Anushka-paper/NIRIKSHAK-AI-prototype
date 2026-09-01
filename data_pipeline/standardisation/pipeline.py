import os
import glob
import pandas as pd
from data_pipeline.standardisation.dates import standardise_date_column
from data_pipeline.standardisation.currency import standardise_currency_column
from data_pipeline.standardisation.categories import standardise_categories
from data_pipeline.standardisation.geography import standardise_geography
from data_pipeline.standardisation.entities import standardise_entities
from data_pipeline.standardisation.statuses import standardise_statuses
from data_pipeline.standardisation.identifiers import standardise_identifiers
from data_pipeline.standardisation.master_model import build_unified_master_model

def standardise_dataset(filepath, dataset_type, house_name):
    print(f"[{house_name}] Standardising {dataset_type} ({os.path.basename(filepath)})...")
    df = pd.read_csv(filepath, low_memory=False)
    
    # Dates
    standardise_date_column(df, "recommended_date", "recommended_date")
    standardise_date_column(df, "sanction_date", "sanction_date")
    standardise_date_column(df, "completion_date", "completion_date")
    standardise_date_column(df, "expenditure_date", "expenditure_date")
    standardise_date_column(df, "date_of_consent", "consent_date")
    
    # Currency
    standardise_currency_column(df, "allocated_amount_₹", "allocated_limit_amount_inr")
    standardise_currency_column(df, "recommended_amount_₹", "recommended_amount_inr")
    standardise_currency_column(df, "sanction_amount_₹", "sanctioned_amount_inr")
    standardise_currency_column(df, "amount_disbursed_₹", "completed_disbursed_amount_inr")
    standardise_currency_column(df, "fund_disbursed_amount_₹", "expenditure_amount_inr")
    standardise_currency_column(df, "consent_amount_₹", "calamity_consent_amount_inr")
    
    # Categories, Geography, Entities, Statuses, Identifiers
    df = standardise_categories(df)
    df = standardise_geography(df, house_name)
    df = standardise_entities(df)
    df = standardise_statuses(df)
    df = standardise_identifiers(df)
    
    out_dir = os.path.join("data", "standardised", house_name.lower())
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"std_{dataset_type}.csv")
    df.to_csv(out_path, index=False, encoding="utf-8")
    return df

def run_standardisation_pipeline():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "cleaned"))
    
    ls_recs, ls_sancs, ls_comps, ls_exps = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    rs_recs, rs_sancs, rs_comps, rs_exps = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    for house in ["lok_sabha", "rajya_sabha"]:
        h_tag = house.upper()
        h_dir = os.path.join(base_dir, house)
        files = glob.glob(os.path.join(h_dir, "clean_*.csv"))
        
        for f in files:
            ds_name = os.path.basename(f).replace("clean_", "").replace(".csv", "")
            df_std = standardise_dataset(f, ds_name, h_tag)
            
            if h_tag == "LOK_SABHA":
                if ds_name == "works_recommended": ls_recs = df_std
                elif ds_name == "works_sanctioned": ls_sancs = df_std
                elif ds_name == "works_completed": ls_comps = df_std
                elif ds_name == "expenditure": ls_exps = df_std
            else:
                if ds_name == "works_recommended": rs_recs = df_std
                elif ds_name == "works_sanctioned": rs_sancs = df_std
                elif ds_name == "works_completed": rs_comps = df_std
                elif ds_name == "expenditure": rs_exps = df_std
                
    # Build Master Models
    all_recs = pd.concat([ls_recs, rs_recs], ignore_index=True)
    all_sancs = pd.concat([ls_sancs, rs_sancs], ignore_index=True)
    all_comps = pd.concat([ls_comps, rs_comps], ignore_index=True)
    all_exps = pd.concat([ls_exps, rs_exps], ignore_index=True)
    
    build_unified_master_model(all_recs, all_sancs, all_comps, all_exps)
    print("[NIRIKSHAK AI] Data Standardisation Pipeline completed successfully!")

if __name__ == "__main__":
    run_standardisation_pipeline()
