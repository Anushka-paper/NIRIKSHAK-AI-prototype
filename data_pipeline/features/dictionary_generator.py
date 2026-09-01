import json
import os
from data_pipeline.features.config import FEATURE_DICTIONARY, FEATURE_VERSION

def generate_feature_dictionary_files(output_dir="data/features"):
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "feature_dictionary.json")
    md_path = os.path.join(output_dir, "feature_dictionary.md")
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"version": FEATURE_VERSION, "dictionary": FEATURE_DICTIONARY}, f, indent=2)
        
    md_lines = ["# Canonical Feature Store Dictionary", f"**Version**: `{FEATURE_VERSION}`\n"]
    for table_name, feats in FEATURE_DICTIONARY.items():
        md_lines.append(f"## Table: `{table_name}`")
        md_lines.append("| Feature Name | Definition | Data Type |")
        md_lines.append("| :--- | :--- | :--- |")
        for f_name, f_def in feats.items():
            dtype = "Float / Numeric" if "pct" in f_name or "delay" in f_name or "gap" in f_name or "score" in f_name else "Integer / String / Boolean"
            md_lines.append(f"| `{f_name}` | {f_def} | `{dtype}` |")
        md_lines.append("")
        
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"[FEATURE DICTIONARY] Exported feature dictionary to {json_path} and {md_path}")
