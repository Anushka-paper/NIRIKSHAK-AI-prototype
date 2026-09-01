import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Reconfigure stdout for Windows console UTF-8 support if available
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def calculate_explainable_quality_score(
    quality_res: dict,
    identifier_res: dict,
    amount_res: dict,
    date_res: dict,
    categorical_res: dict,
    relationship_res: dict
) -> tuple[int, list]:
    """
    Calculates an explainable 0-100 Data Quality Score with itemized issue breakdown.
    """
    score = 100
    issues = []

    dup_rows = quality_res.get("duplicate_rows_count", 0)
    if dup_rows > 0:
        deduction = min(15, dup_rows)
        score -= deduction
        issues.append(f"- {dup_rows} duplicate record rows")
    else:
        issues.append("- 0 duplicate record rows")

    completeness = quality_res.get("completeness_score", 100.0)
    if completeness < 100.0:
        missing_pct = round(100.0 - completeness, 2)
        deduction = min(20, int(missing_pct / 2))
        score -= deduction
        issues.append(f"- {missing_pct}% overall missing values")
    else:
        issues.append("- 0 missing values")

    dup_ids_total = sum(profile.get("duplicate_ids", 0) for profile in identifier_res.values())
    if dup_ids_total > 0:
        score -= 10
        issues.append(f"- {dup_ids_total} duplicate IDs in identifier columns")
    else:
        issues.append("- 0 duplicate IDs")

    neg_amounts_total = sum(profile.get("negative_count", 0) for profile in amount_res.values() if isinstance(profile, dict))
    if neg_amounts_total > 0:
        score -= 10
        issues.append(f"- {neg_amounts_total} negative values in monetary/numeric columns")
    else:
        issues.append("- 0 negative currency values")

    invalid_dates_total = sum(profile.get("invalid_dates", 0) for profile in date_res.get("columns", {}).values())
    seq_anomalies_cnt = len(date_res.get("sequence_anomalies", []))
    if invalid_dates_total > 0 or seq_anomalies_cnt > 0:
        score -= 10
        issues.append(f"- {invalid_dates_total} invalid dates, {seq_anomalies_cnt} date sequence violations")
    else:
        issues.append("- 0 invalid dates or date sequence violations")

    cat_variations_cnt = sum(len(profile.get("possible_category_variations", [])) for profile in categorical_res.values())
    if cat_variations_cnt > 0:
        score -= 5
        issues.append(f"- {cat_variations_cnt} possible category formatting variations")
    else:
        issues.append("- 0 category formatting variations")

    rel_conflicts = sum(res.get("conflicting_child_entities_count", 0) for res in relationship_res.values())
    if rel_conflicts > 0:
        score -= 10
        issues.append(f"- {rel_conflicts} relationship conflicts (conflicting parent entities)")
    else:
        issues.append("- 0 relationship conflicts")

    final_score = max(0, min(100, score))
    return final_score, issues

def build_json_report(
    dataset_name: str,
    parliament: str,
    total_rows: int,
    record_rows: int,
    summary_rows: int,
    total_cols: int,
    schema: list,
    quality_res: dict,
    identifier_res: dict,
    amount_res: dict,
    date_res: dict,
    categorical_res: dict,
    text_res: dict,
    relationship_res: dict,
    mplads_res: dict
) -> dict:
    """Builds structured JSON profiling report for a dataset."""
    score, issues = calculate_explainable_quality_score(
        quality_res, identifier_res, amount_res, date_res, categorical_res, relationship_res
    )

    return {
        "dataset": {
            "name": dataset_name,
            "parliament": parliament,
            "total_rows": total_rows,
            "record_rows": record_rows,
            "summary_rows": summary_rows,
            "columns_count": total_cols
        },
        "schema": schema,
        "missing_values": quality_res.get("missingness_summary", {}),
        "duplicates": {
            "duplicate_rows_count": quality_res.get("duplicate_rows_count", 0),
            "duplicate_rows_pct": quality_res.get("duplicate_rows_pct", 0.0)
        },
        "identifier_profiles": identifier_res,
        "numeric_profiles": amount_res,
        "date_profiles": date_res,
        "categorical_profiles": categorical_res,
        "text_profiles": text_res,
        "relationships": relationship_res,
        "mplads_analysis": mplads_res,
        "data_quality_score": score,
        "data_quality_issues": issues
    }

def print_console_report(report: dict):
    """Prints a clean, readable terminal report matching Section 24 format."""
    ds = report["dataset"]
    print("\n" + "=" * 60)
    print("NIRIKSHAK DYNAMIC DATA PROFILER")
    print("=" * 60)
    print(f"\nParliament: {ds.get('parliament', 'lok_sabha').upper()}")
    print(f"Dataset: {ds['name']}")
    print(f"Total Rows: {ds['total_rows']}")
    print(f"Record Rows: {ds['record_rows']}")
    print(f"Summary Rows Detected: {ds['summary_rows']}")
    print(f"Columns: {ds['columns_count']}")

    print("\n" + "-" * 60)
    print("SCHEMA")
    print("-" * 60)
    for col_info in report.get("schema", []):
        col_name = str(col_info["column_name"]).ljust(35)
        dtype_str = col_info["detected_type"]
        safe_line = f"{col_name} {dtype_str}"
        try:
            print(safe_line)
        except UnicodeEncodeError:
            print(safe_line.encode('ascii', 'replace').decode('ascii'))

    print("\n" + "-" * 60)
    print("DATA QUALITY SCORE")
    print("-" * 60)
    print(f"Score: {report['data_quality_score']}/100")
    print("\nIssues Breakdown:")
    for issue in report.get("data_quality_issues", []):
        try:
            print(f"  {issue}")
        except UnicodeEncodeError:
            print(f"  {issue.encode('ascii', 'replace').decode('ascii')}")

    print("=" * 60 + "\n")

def export_parliament_profiling_artifacts(parliament: str, dataset_reports: dict, output_dir: str | Path):
    """
    Generates all 15 required profiling artifacts inside data/profiling/<parliament>/
    as specified in Section 20:
    1. profiling_report.json
    2. dataset_summary.csv
    3. column_profile.csv
    4. missing_values.csv
    5. duplicate_report.csv
    6. data_type_report.csv
    7. date_quality_report.csv
    8. amount_quality_report.csv
    9. identifier_quality_report.csv
    10. categorical_quality_report.csv
    11. cross_dataset_key_report.csv
    12. relationship_report.csv
    13. chronology_report.csv
    14. outlier_report.csv
    15. profiling_summary.html
    """
    out_p = Path(output_dir) / parliament
    out_p.mkdir(parents=True, exist_ok=True)

    # 1. Save Master profiling_report.json
    master_json = {
        "parliament": parliament,
        "generated_at": datetime.now().isoformat(),
        "total_datasets": len(dataset_reports),
        "datasets": dataset_reports
    }
    with open(out_p / "profiling_report.json", "w", encoding="utf-8") as f:
        json.dump(master_json, f, indent=2)

    # Prepare rows for CSV exports
    summary_rows = []
    col_rows = []
    missing_rows = []
    dup_rows = []
    dtype_rows = []
    date_rows = []
    amount_rows = []
    id_rows = []
    cat_rows = []
    rel_rows = []
    chrono_rows = []
    outlier_rows = []

    for ds_name, rep in dataset_reports.items():
        if "error" in rep:
            continue
        ds_info = rep.get("dataset", {})
        summary_rows.append({
            "parliament": parliament,
            "dataset_name": ds_name,
            "total_rows": ds_info.get("total_rows", 0),
            "record_rows": ds_info.get("record_rows", 0),
            "summary_rows": ds_info.get("summary_rows", 0),
            "columns_count": ds_info.get("columns_count", 0),
            "quality_score": rep.get("data_quality_score", 0)
        })

        for sch in rep.get("schema", []):
            col_name = sch["column_name"]
            col_rows.append({
                "dataset_name": ds_name,
                "column_name": col_name,
                "original_dtype": sch.get("original_dtype"),
                "detected_type": sch.get("detected_type")
            })

            dtype_rows.append({
                "dataset_name": ds_name,
                "column_name": col_name,
                "detected_type": sch.get("detected_type")
            })

        for col_name, miss_info in rep.get("missing_values", {}).items():
            if isinstance(miss_info, dict):
                missing_rows.append({
                    "dataset_name": ds_name,
                    "column_name": col_name,
                    "non_null_count": miss_info.get("non_null_count"),
                    "missing_count": miss_info.get("missing_count"),
                    "missing_pct": miss_info.get("missing_percentage"),
                    "missingness_tier": miss_info.get("missingness_classification")
                })

        dup_info = rep.get("duplicates", {})
        dup_rows.append({
            "dataset_name": ds_name,
            "duplicate_rows_count": dup_info.get("duplicate_rows_count", 0),
            "duplicate_rows_pct": dup_info.get("duplicate_rows_pct", 0.0)
        })

        for col_name, date_info in rep.get("date_profiles", {}).get("columns", {}).items():
            if isinstance(date_info, dict):
                date_rows.append({
                    "dataset_name": ds_name,
                    "column_name": col_name,
                    "missing_dates": date_info.get("missing_dates"),
                    "invalid_dates": date_info.get("invalid_dates"),
                    "future_dates": date_info.get("future_dates"),
                    "min_date": date_info.get("min_date"),
                    "max_date": date_info.get("max_date")
                })

        for seq in rep.get("date_profiles", {}).get("sequence_anomalies", []):
            chrono_rows.append({
                "dataset_name": ds_name,
                "rule": seq.get("rule"),
                "description": seq.get("description"),
                "violation_count": seq.get("violation_count")
            })

        for col_name, amt_info in rep.get("numeric_profiles", {}).items():
            if isinstance(amt_info, dict) and amt_info.get("count", 0) > 0:
                amount_rows.append({
                    "dataset_name": ds_name,
                    "column_name": col_name,
                    "count": amt_info.get("count"),
                    "min": amt_info.get("minimum"),
                    "max": amt_info.get("maximum"),
                    "mean": amt_info.get("mean"),
                    "median": amt_info.get("median"),
                    "zero_count": amt_info.get("zero_count"),
                    "negative_count": amt_info.get("negative_count"),
                    "outlier_count": amt_info.get("outliers", {}).get("outlier_count", 0)
                })

                outlier_info = amt_info.get("outliers", {})
                if outlier_info.get("outlier_count", 0) > 0:
                    outlier_rows.append({
                        "dataset_name": ds_name,
                        "column_name": col_name,
                        "outlier_count": outlier_info.get("outlier_count"),
                        "outlier_pct": outlier_info.get("outlier_percentage"),
                        "lower_bound": outlier_info.get("lower_bound"),
                        "upper_bound": outlier_info.get("upper_bound")
                    })

        for col_name, id_info in rep.get("identifier_profiles", {}).items():
            if isinstance(id_info, dict):
                id_rows.append({
                    "dataset_name": ds_name,
                    "column_name": col_name,
                    "unique_ids": id_info.get("unique_ids"),
                    "duplicate_ids": id_info.get("duplicate_ids"),
                    "missing_ids": id_info.get("missing_ids"),
                    "uniqueness_ratio_pct": id_info.get("uniqueness_ratio_pct")
                })

        for col_name, cat_info in rep.get("categorical_profiles", {}).items():
            if isinstance(cat_info, dict):
                cat_rows.append({
                    "dataset_name": ds_name,
                    "column_name": col_name,
                    "unique_values": cat_info.get("unique_values"),
                    "missing_values": cat_info.get("missing_values"),
                    "rare_categories_count": cat_info.get("rare_categories_count"),
                    "category_variations_found": len(cat_info.get("possible_category_variations", []))
                })

        for rel_key, rel_info in rep.get("relationships", {}).items():
            if isinstance(rel_info, dict):
                rel_rows.append({
                    "dataset_name": ds_name,
                    "relationship": rel_key,
                    "parent_entities": rel_info.get("total_parent_entities"),
                    "child_entities": rel_info.get("total_child_entities"),
                    "conflicts_count": rel_info.get("conflicting_child_entities_count")
                })

    # Save CSV reports
    pd.DataFrame(summary_rows).to_csv(out_p / "dataset_summary.csv", index=False)
    pd.DataFrame(col_rows).to_csv(out_p / "column_profile.csv", index=False)
    pd.DataFrame(missing_rows).to_csv(out_p / "missing_values.csv", index=False)
    pd.DataFrame(dup_rows).to_csv(out_p / "duplicate_report.csv", index=False)
    pd.DataFrame(dtype_rows).to_csv(out_p / "data_type_report.csv", index=False)
    pd.DataFrame(date_rows).to_csv(out_p / "date_quality_report.csv", index=False)
    pd.DataFrame(amount_rows).to_csv(out_p / "amount_quality_report.csv", index=False)
    pd.DataFrame(id_rows).to_csv(out_p / "identifier_quality_report.csv", index=False)
    pd.DataFrame(cat_rows).to_csv(out_p / "categorical_quality_report.csv", index=False)
    pd.DataFrame(rel_rows).to_csv(out_p / "relationship_report.csv", index=False)
    pd.DataFrame(chrono_rows).to_csv(out_p / "chronology_report.csv", index=False)
    pd.DataFrame(outlier_rows).to_csv(out_p / "outlier_report.csv", index=False)

    # 11. Cross Dataset Key Report (Overlap Analysis)
    cross_rows = []
    dataset_names = list(dataset_reports.keys())
    for i in range(len(dataset_names)):
        for j in range(i + 1, len(dataset_names)):
            dsA, dsB = dataset_names[i], dataset_names[j]
            repA, repB = dataset_reports[dsA], dataset_reports[dsB]
            colsA = {s["column_name"] for s in repA.get("schema", [])}
            colsB = {s["column_name"] for s in repB.get("schema", [])}
            common_cols = list(colsA.intersection(colsB))
            for k in common_cols:
                cross_rows.append({
                    "dataset_a": dsA,
                    "dataset_b": dsB,
                    "common_key": k
                })
    pd.DataFrame(cross_rows).to_csv(out_p / "cross_dataset_key_report.csv", index=False)

    # 15. Save profiling_summary.html
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>NIRIKSHAK Data Profiling Summary - {parliament.upper()}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f8fafc; color: #0f172a; }}
        h1 {{ color: #1e3a8a; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 10px; background: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        th, td {{ border: 1px solid #cbd5e1; padding: 10px; text-align: left; }}
        th {{ background-color: #f1f5f9; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-weight: bold; color: white; }}
        .passed {{ background-color: #16a34a; }}
        .warning {{ background-color: #d97706; }}
    </style>
</head>
<body>
    <h1>NIRIKSHAK Data Quality Executive Audit - {parliament.upper()}</h1>
    <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <h2>Dataset Overview</h2>
    <table>
        <tr><th>Dataset Name</th><th>Total Rows</th><th>Record Rows</th><th>Summary Rows</th><th>Columns</th><th>Quality Score</th></tr>
"""
    for r in summary_rows:
        score = r["quality_score"]
        badge_cls = "passed" if score >= 85 else "warning"
        html_content += f"<tr><td>{r['dataset_name']}</td><td>{r['total_rows']}</td><td>{r['record_rows']}</td><td>{r['summary_rows']}</td><td>{r['columns_count']}</td><td><span class='badge {badge_cls}'>{score}/100</span></td></tr>"

    html_content += """
    </table>
</body>
</html>"""

    with open(out_p / "profiling_summary.html", "w", encoding="utf-8") as f:
        f.write(html_content)
