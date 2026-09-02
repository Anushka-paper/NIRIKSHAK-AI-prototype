import os
from data_pipeline.validation.engine import ValidationEngine
from data_pipeline.validation.reports import generate_validation_reports

def run_validation_pipeline():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "cleaned"))
    
    ls_cleaned_dir = os.path.join(base_dir, "lok_sabha")
    rs_cleaned_dir = os.path.join(base_dir, "rajya_sabha")
    
    print("==========================================")
    print("Starting LOK SABHA Data Validation...")
    print("==========================================")
    ls_engine = ValidationEngine("LOK_SABHA", ls_cleaned_dir)
    ls_metrics = ls_engine.validate_all()
    
    print("==========================================")
    print("Starting RAJYA SABHA Data Validation...")
    print("==========================================")
    rs_engine = ValidationEngine("RAJYA_SABHA", rs_cleaned_dir)
    rs_metrics = rs_engine.validate_all()
    
    generate_validation_reports(ls_metrics, rs_metrics)
    print("[NIRIKSHAK AI] Data Validation Pipeline completed successfully for BOTH Lok Sabha & Rajya Sabha datasets!")

if __name__ == "__main__":
    run_validation_pipeline()
