import os
import pandas as pd
from data_pipeline.entity_resolution.normalizers import normalize_vendor

def resolve_vendor_entities(df_master):
    print("[ENTITY RESOLUTION] Resolving Vendor & Contractor entities...")
    vendors = []
    aliases = []
    seen_vendors = {}
    
    if "canonical_vendor_name" not in df_master.columns:
        return pd.DataFrame(), pd.DataFrame()
        
    v_df = df_master.dropna(subset=["canonical_vendor_name"])[["canonical_vendor_name", "canonical_state", "expenditure_amount_inr"]].copy()
    
    for idx, row in v_df.iterrows():
        raw_v = str(row["canonical_vendor_name"]).strip()
        if not raw_v or raw_v.upper() == "NAN":
            continue
        norm_v = normalize_vendor(raw_v)
        state = str(row.get("canonical_state", "")).strip()
        amt = float(row.get("expenditure_amount_inr", 0) or 0)
        
        key = norm_v
        if key not in seen_vendors:
            v_id = f"VENDOR_{len(seen_vendors) + 1:06d}"
            seen_vendors[key] = {
                "vendor_id": v_id,
                "canonical_name": raw_v.upper(),
                "normalized_name": norm_v,
                "canonical_state": state,
                "total_expenditure_inr": amt,
                "works_count": 1
            }
            aliases.append({
                "alias_id": f"VENDOR_ALIAS_{len(aliases) + 1:06d}",
                "vendor_id": v_id,
                "original_name": raw_v,
                "normalized_name": norm_v,
                "confidence_score": 1.0,
                "verified": True
            })
        else:
            seen_vendors[key]["total_expenditure_inr"] += amt
            seen_vendors[key]["works_count"] += 1
            
    df_vendors = pd.DataFrame(list(seen_vendors.values()))
    df_aliases = pd.DataFrame(aliases)
    
    out_dir = os.path.join("data", "entity_resolution", "master")
    os.makedirs(out_dir, exist_ok=True)
    df_vendors.to_csv(os.path.join(out_dir, "vendor_master.csv"), index=False, encoding="utf-8")
    
    alias_dir = os.path.join("data", "entity_resolution", "alias")
    os.makedirs(alias_dir, exist_ok=True)
    df_aliases.to_csv(os.path.join(alias_dir, "vendor_alias.csv"), index=False, encoding="utf-8")
    
    print(f"[ENTITY RESOLUTION] Resolved {len(df_vendors):,} unique Vendor master entities.")
    return df_vendors, df_aliases
