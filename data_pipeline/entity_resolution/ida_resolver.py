import os
import pandas as pd
from data_pipeline.entity_resolution.normalizers import normalize_ida

def resolve_ida_entities(df_master):
    print("[ENTITY RESOLUTION] Resolving Implementing District Authorities (IDAs)...")
    idas = []
    aliases = []
    seen_idas = {}
    
    # Extract IDAs from master if present
    ida_names = []
    if "canonical_ida" in df_master.columns:
        ida_names = df_master["canonical_ida"].dropna().unique().tolist()
        
    for raw_ida in ida_names:
        norm_ida = normalize_ida(str(raw_ida))
        if norm_ida not in seen_idas:
            ida_id = f"IDA_{len(seen_idas) + 1:06d}"
            seen_idas[norm_ida] = ida_id
            idas.append({
                "ida_id": ida_id,
                "canonical_name": str(raw_ida).upper(),
                "normalized_name": norm_ida,
                "agency_type": "DISTRICT_AUTHORITY",
                "created_at": pd.Timestamp.now().isoformat()
            })
            aliases.append({
                "alias_id": f"IDA_ALIAS_{len(aliases) + 1:06d}",
                "ida_id": ida_id,
                "original_name": str(raw_ida),
                "normalized_name": norm_ida,
                "confidence_score": 1.0,
                "verified": True
            })
            
    df_idas = pd.DataFrame(idas)
    df_aliases = pd.DataFrame(aliases)
    
    out_dir = os.path.join("data", "entity_resolution", "master")
    os.makedirs(out_dir, exist_ok=True)
    df_idas.to_csv(os.path.join(out_dir, "ida_master.csv"), index=False, encoding="utf-8")
    
    alias_dir = os.path.join("data", "entity_resolution", "alias")
    os.makedirs(alias_dir, exist_ok=True)
    df_aliases.to_csv(os.path.join(alias_dir, "ida_alias.csv"), index=False, encoding="utf-8")
    
    print(f"[ENTITY RESOLUTION] Resolved {len(df_idas):,} unique IDA master entities.")
    return df_idas, df_aliases
