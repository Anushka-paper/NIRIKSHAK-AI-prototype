import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os

print("Loading SentenceTransformer model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embeddings():
    print("Reading Lok Sabha canonical works...")
    df = pd.read_csv("data/features/lok_sabha/canonical_work_features.csv")
    
    # Take a sample of 2000 works to keep the prototype fast
    # Prioritize works that have a valid description
    df = df.dropna(subset=["description"])
    df = df.head(2000)
    
    print(f"Generating embeddings for {len(df)} works. This might take a minute...")
    descriptions = df["description"].tolist()
    
    # Compute embeddings
    embeddings = model.encode(descriptions, show_progress_bar=True)
    
    # Save the embeddings and the corresponding IDs/metadata
    print("Saving embeddings to artifacts...")
    os.makedirs("artifacts", exist_ok=True)
    
    data = {
        "ids": df["work_id"].tolist(),
        "descriptions": descriptions,
        "mp_name": df["mp_id"].tolist(),
        "state": df["state"].tolist(),
        "cost": df["recommended_amount"].tolist(),
        "embeddings": embeddings
    }
    
    with open("artifacts/work_embeddings.pkl", "wb") as f:
        pickle.dump(data, f)
        
    print("Embeddings generated and saved successfully!")

if __name__ == "__main__":
    generate_embeddings()
