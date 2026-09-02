import os
import pandas as pd
from data_pipeline.entity_resolution.normalizers import normalize_name

def resolve_mp_entities(df_master):
    print("[ENTITY RESOLUTION] Resolving Members of Parliament (MPs)...")
    mps = []
    aliases = []
    seen_mps = {}
    
    req_cols = ["source_house", "canonical_mp_name", "canonical_state", "canonical_constituency"]
    avail = [c for c in req_cols if c in df_master.columns]
    
    mp_df = df_master[avail].drop_duplicates()
    
    for idx, row in mp_df.iterrows():
        raw_name = str(row.get("canonical_mp_name", "")).strip()
        if not raw_name or raw_name.upper() == "NAN":
            continue
        house = str(row.get("source_house", "")).strip()
        state = str(row.get("canonical_state", "")).strip()
        const = str(row.get("canonical_constituency", "")).strip()
        norm_name = normalize_name(raw_name)
        
        key = f"{house}_{state}_{norm_name}"
        if key not in seen_mps:
            mp_id = f"MP_{len(seen_mps) + 1:06d}"
            seen_mps[key] = mp_id
            mps.append({
                "mp_id": mp_id,
                "canonical_name": raw_name.upper(),
                "normalized_name": norm_name,
                "source_house": house,
                "canonical_state": state,
                "canonical_constituency": const,
                "created_at": pd.Timestamp.now().isoformat()
            })
            aliases.append({
                "alias_id": f"MP_ALIAS_{len(aliases) + 1:06d}",
                "mp_id": mp_id,
                "original_name": raw_name,
                "normalized_name": norm_name,
                "confidence_score": 1.0,
                "verified": True
            })
            
    df_mps = pd.DataFrame(mps)
    df_aliases = pd.DataFrame(aliases)
    
    out_dir = os.path.join("data", "entity_resolution", "master")
    os.makedirs(out_dir, exist_ok=True)
    df_mps.to_csv(os.path.join(out_dir, "mp_master.csv"), index=False, encoding="utf-8")
    
    alias_dir = os.path.join("data", "entity_resolution", "alias")
    os.makedirs(alias_dir, exist_ok=True)
    df_aliases.to_csv(os.path.join(alias_dir, "mp_alias.csv"), index=False, encoding="utf-8")
    
    print(f"[ENTITY RESOLUTION] Resolved {len(df_mps):,} unique MP master entities.")
    return df_mps, df_aliases
