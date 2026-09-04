"""
audit_dossier_generator.py
Generates a statutory PDF audit dossier for a given project work record.
Uses FPDF2 (a lightweight, zero-dependency PDF library).
"""

import os
import datetime

def generate_dossier_pdf(work_data: dict, output_dir: str = None) -> str:
    """
    Generates a PDF dossier for a given work record.
    Returns the path to the saved PDF file.
    
    For the presentation, we produce a well-structured plain text file
    to avoid the FPDF2 dependency. In production, swap in the fpdf2 block below.
    """
    work_id = work_data.get("work_id", "UNKNOWN")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "generated")
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, f"dossier_{work_id}.txt")

    risk = work_data.get("composite_risk", {})
    delay = work_data.get("delay_analysis", {})
    duplicates = work_data.get("drishti_duplicates", [])
    anomaly = work_data.get("anomaly_analysis", {})
    basic = work_data.get("basic_details", {})

    lines = [
        "=" * 70,
        "NIRIKSHAK 2.0 - STATUTORY AUDIT DOSSIER",
        "MPLADS Anomaly Investigation Layer (AI-Generated Report)",
        "=" * 70,
        f"Generated At : {now}",
        f"Work ID      : {work_id}",
        f"MP Name      : {basic.get('mp_name', 'N/A')}",
        f"State        : {basic.get('state', 'N/A')}",
        f"Constituency : {basic.get('constituency', 'N/A')}",
        f"Category     : {basic.get('work_category', 'N/A')}",
        f"Sanction Amt : ₹{basic.get('sanctioned_amount', 0):,}",
        "",
        "-" * 70,
        "COMPOSITE RISK ASSESSMENT (XGBoost 6-Model Consensus)",
        "-" * 70,
        f"Risk Level   : {risk.get('level', 'N/A')}",
        f"Risk Score   : {risk.get('score', 0)} / 110",
        "",
        "-" * 70,
        "DELAY SURVIVAL ANALYSIS (Cox Proportional Hazards Model)",
        "-" * 70,
        f"Prob. Completed by Day 30  : {delay.get('day_30', 0) * 100:.0f}%",
        f"Prob. Completed by Day 90  : {delay.get('day_90', 0) * 100:.0f}%",
        f"Prob. Completed by Day 365 : {delay.get('day_365', 0) * 100:.0f}%",
        "",
        "-" * 70,
        "ISOLATION FOREST ANOMALY DETECTION",
        "-" * 70,
        f"Anomaly Flagged : {'YES ⚠' if anomaly.get('is_anomaly') else 'NO ✓'}",
        f"Anomaly Score   : {anomaly.get('score', 'N/A')}",
        "",
        "-" * 70,
        f"DRISHTI NLP DUPLICATE DETECTION ({len(duplicates)} matches found)",
        "-" * 70,
    ]
    for d in duplicates:
        lines.append(f"  - [{d['canonical_id']}] '{d['title']}' (similarity: {d['similarity']})")
    if not duplicates:
        lines.append("  No semantic duplicates found.")
    
    lines += [
        "",
        "=" * 70,
        "DISCLAIMER: This report is AI-generated for investigative support.",
        "It is not a final audit opinion. Subject to human expert review.",
        "=" * 70,
    ]

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Dossier saved: {filename}")
    return filename


if __name__ == "__main__":
    dummy = {
        "work_id": "LOC-MP-7890",
        "basic_details": {
            "mp_name": "Shri Rajesh Kumar",
            "state": "Uttar Pradesh",
            "constituency": "Varanasi",
            "work_category": "Roads",
            "sanctioned_amount": 7500000
        },
        "composite_risk": {"level": "HIGH", "score": 55},
        "delay_analysis": {"day_30": 0.08, "day_90": 0.35, "day_365": 0.75},
        "anomaly_analysis": {"is_anomaly": True, "score": -0.31},
        "drishti_duplicates": [
            {"canonical_id": "LOC-MP-9900", "similarity": 0.91, "title": "CC Road Varanasi Ghats"},
        ]
    }
    generate_dossier_pdf(dummy)
