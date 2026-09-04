import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(PROJECT_ROOT, "ml_models"))

from anomaly_detection_module import AnomalyDetector
from delay_prediction_module import DelayPredictionModel
from sentence_bert_model import SentenceBertModel
from xgboost_risk_scoring_module import XGBoostRiskScoringModel

class UnifiedSyncOrchestrator:
    def __init__(self):
        print("Initializing Unified Sync Orchestrator...")
        # In a real app we'd load joblib models here. We'll instantiate our classes for the simulation.
        self.delay_model = DelayPredictionModel()
        self.sbert_model = SentenceBertModel()
        self.xgb_model = XGBoostRiskScoringModel()
        # Assume trained
        
    def sync_work_record(self, work_data: dict, description: str):
        """
        Orchestrates 6 ML models to output a composite risk dossier profile.
        """
        print(f"Orchestrating ML consensus for work: {work_data.get('work_id')}")
        
        # 1. Delay Probability (CoxPH)
        delay_probs = self.delay_model.predict_survival(work_data)
        
        # 2. Duplicate Detection (SBERT)
        duplicates = self.sbert_model.check_duplicate(description)
        duplicate_found = len(duplicates) > 0
        
        # 3. Anomaly Detection (Isolation Forest)
        # Assuming work_data already has 'anomaly_flag' from our project_investigations table
        is_anomaly = work_data.get("anomaly_flag", False)
        
        # 4. Final Risk Scoring (XGBoost)
        signals = {
            "is_anomaly": is_anomaly,
            "delay_prob_365": delay_probs["day_365"],
            "duplicate_found": duplicate_found
        }
        composite_risk = self.xgb_model.predict_risk(signals)
        
        return {
            "work_id": work_data.get("work_id"),
            "basic_details": work_data,
            "delay_analysis": delay_probs,
            "drishti_duplicates": duplicates,
            "anomaly_analysis": {
                "is_anomaly": is_anomaly,
                "score": work_data.get("anomaly_score")
            },
            "composite_risk": composite_risk
        }

if __name__ == "__main__":
    orchestrator = UnifiedSyncOrchestrator()
    dummy_work = {"work_id": "LOC-MP-123", "sanctioned_amount": 5000000, "anomaly_flag": True}
    res = orchestrator.sync_work_record(dummy_work, "Construction of school")
    print(res)
