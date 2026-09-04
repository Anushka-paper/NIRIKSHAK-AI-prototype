import os
import joblib

class SentenceBertModel:
    def __init__(self):
        self.model = None

    def train(self, data):
        # We simulate this to avoid the 400MB download during the presentation.
        print("Training Sentence-BERT Model (DRISHTI Simulation)...")
        self.model = "sbert_model_trained"
        
        models_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(models_dir, exist_ok=True)
        joblib.dump(self, os.path.join(models_dir, 'sentence_bert_model.joblib'))
        print("Sentence-BERT Model saved.")

    def check_duplicate(self, query: str):
        """
        Simulate a cosine similarity match against an embedded database of projects.
        """
        # Simulated responses
        if "school" in query.lower() or "education" in query.lower():
            return [
                {"canonical_id": "LOC-MP-1234", "similarity": 0.88, "title": "Construction of primary school in Sector 5", "status": "COMPLETED"},
                {"canonical_id": "LOC-MP-4321", "similarity": 0.82, "title": "Boundary wall for Sector 5 school", "status": "ONGOING"}
            ]
        elif "road" in query.lower() or "cc" in query.lower():
            return [
                {"canonical_id": "LOC-MP-9988", "similarity": 0.94, "title": "CC Road from Main Highway to Village Center", "status": "COMPLETED"}
            ]
        else:
            return []

if __name__ == "__main__":
    model = SentenceBertModel()
    model.train([])
