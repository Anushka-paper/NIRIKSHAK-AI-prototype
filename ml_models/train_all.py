import os
import sys
import pandas as pd
import duckdb
import joblib
import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "ml_models"))

from anomaly_detection_module import AnomalyDetector
from forecasting_module import ExpenditureForecaster
from vendor_collusion_graph_module import VendorCollusionGraph
from delay_prediction_module import DelayPredictionModel
from sentence_bert_model import SentenceBertModel
from xgboost_risk_scoring_module import XGBoostRiskScoringModel

DB_PATH = os.path.join(PROJECT_ROOT, "data_pipeline", "parliament_data.duckdb")
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts")

def main():
    print("=" * 60)
    print("NIRIKSHAK 2.0 - Full 6-Model Training Pipeline")
    print("=" * 60)
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}. Run ETL pipeline first.")
        return

    # Load data
    print("\n[1/7] Loading Data from DuckDB...")
    conn = duckdb.connect(DB_PATH)
    try:
        df = conn.execute("SELECT * FROM loksabha_expenditure").fetchdf()
    except Exception as e:
        print(f"Could not read loksabha_expenditure: {e}")
        conn.close()
        return

    if df.empty:
        print("Dataframe is empty. Aborting.")
        conn.close()
        return

    print(f"  Loaded {len(df):,} records.")

    # 1. Anomaly Detection (Isolation Forest)
    print("\n[2/7] Training Isolation Forest (Anomaly Detection)...")
    features = ['amount_disbursed', 'vendor_frequency', 'delay_days']
    anomaly_detector = AnomalyDetector()
    anomaly_detector.train(df, features)
    anomaly_detector.save(os.path.join(ARTIFACTS_DIR, "anomaly_detector"))
    
    # Score and save anomalies to DuckDB
    print("   Scoring records and saving to DuckDB...")
    scored_df = anomaly_detector.predict(df, features)
    conn.execute("CREATE OR REPLACE TABLE anomaly_results AS SELECT * FROM scored_df")
    print(f"   Saved {len(scored_df)} scored records.")

    # 2. Prophet Forecasting
    print("\n[3/7] Training Prophet (Expenditure Forecasting)...")
    forecaster = ExpenditureForecaster()
    prophet_df = forecaster.prepare_data(df, date_col='date', amount_col='amount_disbursed')
    forecaster.train(prophet_df)
    forecaster.save(os.path.join(ARTIFACTS_DIR, "forecaster.joblib"))

    # 3. Vendor Collusion Graph (NetworkX)
    print("\n[4/7] Building Vendor Collusion Graph (NetworkX)...")
    graph_module = VendorCollusionGraph()
    graph_module.build_graph(df, project_col='project_id', vendor_col='vendor_id')
    graph_module.save(os.path.join(ARTIFACTS_DIR, "vendor_graph.joblib"))

    # 4. Delay Prediction (CoxPH Simulation)
    print("\n[5/7] Training Delay Prediction Model (CoxPH)...")
    delay_model = DelayPredictionModel()
    delay_model.train(df)

    # 5. Sentence-BERT Duplicate Detection
    print("\n[6/7] Training DRISHTI NLP Model (Sentence-BERT)...")
    sbert_model = SentenceBertModel()
    sbert_model.train(df.get("work_description", pd.Series([])).tolist())

    # 6. XGBoost Unified Risk Scoring
    print("\n[7/7] Training XGBoost Risk Scoring Model...")
    xgb_model = XGBoostRiskScoringModel()
    xgb_model.train(df)

    conn.close()
    
    # Write training timestamp
    ts_file = os.path.join(PROJECT_ROOT, "data_pipeline", ".last_scraped")
    with open(ts_file, "w") as f:
        f.write(datetime.datetime.now().isoformat())
    
    print("\n" + "=" * 60)
    print("Training Complete! All 6 models saved to /artifacts/")
    print("Timestamp written to .last_scraped")
    print("=" * 60)

if __name__ == "__main__":
    main()
