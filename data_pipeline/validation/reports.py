import os
import json

def generate_validation_reports(ls_metrics, rs_metrics):
    reports_dir = os.path.join("data", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    with open(os.path.join(reports_dir, "lok_sabha_validation_report.json"), "w", encoding="utf-8") as f:
        json.dump(ls_metrics, f, indent=2)
        
    with open(os.path.join(reports_dir, "rajya_sabha_validation_report.json"), "w", encoding="utf-8") as f:
        json.dump(rs_metrics, f, indent=2)

    md = "# MPLADS Data Validation & Quality Assessment Report\n\n"
    md += "## Executive Summary\n"
    md += "This report presents empirical Data Quality scores, rule execution counts, null profiles, and validation metrics computed independently for **Lok Sabha** and **Rajya Sabha** datasets post-cleaning.\n\n---\n\n"
    md += "## Data Validation Comparison Matrix\n\n"
    md += "| Metric | Lok Sabha (LOK_SABHA) | Rajya Sabha (RAJYA_SABHA) | Combined System |\n"
    md += "| :--- | :---: | :---: | :---: |\n"
    
    ls_rows = ls_metrics["total_rows"]
    rs_rows = rs_metrics["total_rows"]
    ls_err = ls_metrics["total_errors"]
    rs_err = rs_metrics["total_errors"]
    ls_warn = ls_metrics["total_warnings"]
    rs_warn = rs_metrics["total_warnings"]
    
    md += f"| **Total Validated Records** | {ls_rows:,} | {rs_rows:,} | {ls_rows + rs_rows:,} |\n"
    md += f"| **Total Validation Errors** | {ls_err} | {rs_err} | {ls_err + rs_err} |\n"
    md += f"| **Total Validation Warnings** | {ls_warn} | {rs_warn} | {ls_warn + rs_warn} |\n"
    md += f"| **Overall Quality Score** | **{ls_metrics['quality_score']}%** | **{rs_metrics['quality_score']}%** | **{round((ls_metrics['quality_score'] + rs_metrics['quality_score'])/2, 2)}%** |\n\n"

    md += "## Detailed Dataset Breakdown\n\n"
    md += "### Lok Sabha Datasets\n\n"
    md += "| Dataset | Total Rows | Errors | Warnings | Quality Status |\n"
    md += "| :--- | :---: | :---: | :---: | :---: |\n"
    for d, m in ls_metrics["datasets"].items():
        md += f"| `{d}` | {m['rows']:,} | {m['errors']} | {m['warnings']} | **{m['status']}** |\n"

    md += "\n### Rajya Sabha Datasets\n\n"
    md += "| Dataset | Total Rows | Errors | Warnings | Quality Status |\n"
    md += "| :--- | :---: | :---: | :---: | :---: |\n"
    for d, m in rs_metrics["datasets"].items():
        md += f"| `{d}` | {m['rows']:,} | {m['errors']} | {m['warnings']} | **{m['status']}** |\n"

    with open(os.path.join(reports_dir, "combined_validation_comparison.md"), "w", encoding="utf-8") as f:
        f.write(md)
        
    print(f"[NIRIKSHAK AI] Data Validation Reports successfully saved to {reports_dir}")
