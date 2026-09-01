import pandas as pd
import numpy as np
from faker import Faker
import random
import os
import uuid
from datetime import datetime, timedelta

# Fix random seed for reproducibility
np.random.seed(42)
random.seed(42)
fake = Faker('en_IN')
Faker.seed(42)

NUM_WORKS = 2500
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'raw_csvs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Base Dimensions
STATES = ["Maharashtra", "Karnataka", "Delhi", "Tamil Nadu", "Gujarat"]
CATEGORIES = [
    "Drinking Water", "Education", "Electricity", "Health", 
    "Roads", "Sanitation", "Sports", "Railways"
]

def generate_dimensions():
    # Geography
    geo_data = []
    geo_id = 1
    state_ids = {}
    for state in STATES:
        geo_data.append({"geo_id": geo_id, "level": "state", "name": state, "parent_geo_id": None})
        state_ids[state] = geo_id
        geo_id += 1
        
    constituencies = []
    for state in STATES:
        for _ in range(5):
            c_name = fake.city()
            geo_data.append({"geo_id": geo_id, "level": "constituency", "name": c_name, "parent_geo_id": state_ids[state]})
            constituencies.append({"geo_id": geo_id, "state_id": state_ids[state], "name": c_name})
            geo_id += 1
            
    geo_df = pd.DataFrame(geo_data)
    geo_df.to_csv(os.path.join(OUTPUT_DIR, "Geography.csv"), index=False)
    
    # MP Master
    mp_data = []
    for i, c in enumerate(constituencies):
        mp_data.append({
            "mp_id": i + 1,
            "canonical_name": fake.name(),
            "state_id": c["state_id"],
            "constituency_id": c["geo_id"],
            "created_at": datetime.now().isoformat()
        })
    mp_df = pd.DataFrame(mp_data)
    mp_df.to_csv(os.path.join(OUTPUT_DIR, "MP_Master.csv"), index=False)
    
    # Vendor Master
    vendor_data = []
    for i in range(200):
        vendor_data.append({
            "vendor_id": i + 1,
            "canonical_name": f"{fake.company()} Constructions",
            "created_at": datetime.now().isoformat()
        })
    vendor_df = pd.DataFrame(vendor_data)
    vendor_df.to_csv(os.path.join(OUTPUT_DIR, "Vendor_Master.csv"), index=False)
    
    # IDA Master
    ida_data = []
    for i in range(20):
        ida_data.append({
            "ida_id": i + 1,
            "name": f"District Authority {fake.city()}",
            "state_id": random.choice(list(state_ids.values()))
        })
    pd.DataFrame(ida_data).to_csv(os.path.join(OUTPUT_DIR, "IDA_Master.csv"), index=False)
    
    return mp_df, vendor_df, pd.DataFrame(ida_data)

def generate_works(mp_df, vendor_df, ida_df):
    works = []
    sanctions = []
    expenditures = []
    completions = []
    ground_truth = []
    
    # Generate works
    for i in range(1, NUM_WORKS + 1):
        mp = mp_df.sample(1).iloc[0]
        ida = ida_df.sample(1).iloc[0]
        category = random.choice(CATEGORIES)
        
        # Base realistic amounts (in paise, so multiply by 100)
        # e.g., 5 Lakhs to 50 Lakhs
        base_amount_inr = random.randint(5_00, 50_00) * 1000
        recommended_amount = base_amount_inr * 100
        
        # Introduce dirty data: Composite Work ID
        work_id_raw = f"{category[:3].upper()}-{mp['constituency_id']}-{2023}-{i:04d}"
        if random.random() < 0.05:
            # Dirty ID
            work_id_raw = f"{work_id_raw}_{category}"
            
        description = f"Construction of {category.lower()} facility at {fake.street_name()}"
        
        # Anomalies
        is_cost_overrun = False
        is_expenditure_before_sanction = False
        is_delayed = False
        
        if random.random() < 0.10: # 10% chance of anomaly
            anomaly_type = random.choice(['cost_overrun', 'early_expenditure', 'delayed'])
            if anomaly_type == 'cost_overrun':
                is_cost_overrun = True
                ground_truth.append({"work_id": i, "anomaly_type": "cost_overrun"})
            elif anomaly_type == 'early_expenditure':
                is_expenditure_before_sanction = True
                ground_truth.append({"work_id": i, "anomaly_type": "early_expenditure"})
            elif anomaly_type == 'delayed':
                is_delayed = True
                ground_truth.append({"work_id": i, "anomaly_type": "delayed"})
        
        rec_date = fake.date_between(start_date='-3y', end_date='-1y')
        
        works.append({
            "work_id": i,
            "work_id_raw": work_id_raw,
            "mp_id": mp['mp_id'],
            "ida_id": ida['ida_id'],
            "category": category,
            "description": description,
            "recommended_amount": recommended_amount,
            "recommendation_date": rec_date.isoformat()
        })
        
        # Sanctions
        sanc_delay = random.randint(10, 60)
        sanc_date = rec_date + timedelta(days=sanc_delay)
        
        sanctioned_amount = recommended_amount
        if is_cost_overrun:
            sanctioned_amount = int(recommended_amount * random.uniform(1.5, 2.5))
            
        sanctions.append({
            "work_id": i,
            "sanctioned_amount": sanctioned_amount,
            "sanction_date": sanc_date.isoformat()
        })
        
        # Expenditures
        num_txns = random.randint(1, 4)
        total_spent = 0
        vendor = vendor_df.sample(1).iloc[0]
        
        for t in range(num_txns):
            txn_amount = int(sanctioned_amount / num_txns)
            
            if is_expenditure_before_sanction and t == 0:
                txn_date = sanc_date - timedelta(days=random.randint(5, 20))
            else:
                txn_date = sanc_date + timedelta(days=random.randint(10, 300))
                
            expenditures.append({
                "txn_id": len(expenditures) + 1,
                "work_id": i,
                "vendor_id": vendor['vendor_id'],
                "amount": txn_amount,
                "txn_date": txn_date.isoformat(),
                "payment_status": "Completed"
            })
            total_spent += txn_amount
            
        # Completion
        is_completed = random.random() > 0.3
        if is_completed and not is_delayed:
            comp_date = sanc_date + timedelta(days=random.randint(90, 180))
            completions.append({
                "work_id": i,
                "completion_date": comp_date.isoformat(),
                "status": "Completed",
                "has_completion_evidence": random.random() > 0.1
            })
        elif is_completed and is_delayed:
            comp_date = sanc_date + timedelta(days=random.randint(400, 800))
            completions.append({
                "work_id": i,
                "completion_date": comp_date.isoformat(),
                "status": "Completed",
                "has_completion_evidence": True
            })
            
    pd.DataFrame(works).to_csv(os.path.join(OUTPUT_DIR, "Works_Recommended.csv"), index=False)
    pd.DataFrame(sanctions).to_csv(os.path.join(OUTPUT_DIR, "Works_Sanctioned.csv"), index=False)
    pd.DataFrame(expenditures).to_csv(os.path.join(OUTPUT_DIR, "Expenditure.csv"), index=False)
    pd.DataFrame(completions).to_csv(os.path.join(OUTPUT_DIR, "Works_Completed.csv"), index=False)
    pd.DataFrame(ground_truth).to_csv(os.path.join(OUTPUT_DIR, "Ground_Truth.csv"), index=False)
    
if __name__ == "__main__":
    print("Generating synthetic dimensions...")
    mp, v, ida = generate_dimensions()
    print("Generating works and anomalies...")
    generate_works(mp, v, ida)
    print(f"Data generation complete. Saved to {OUTPUT_DIR}")
