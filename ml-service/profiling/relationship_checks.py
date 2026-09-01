import pandas as pd

def find_column_by_keyword(df: pd.DataFrame, keywords: list) -> str | None:
    """Finds first matching column name based on list of keywords."""
    for col in df.columns:
        col_clean = col.lower().strip()
        if any(k in col_clean for k in keywords):
            return col
    return None

def profile_hierarchical_relationship(df: pd.DataFrame, parent_col: str, child_col: str) -> dict | None:
    """
    Analyzes parent-child entity mapping (e.g. State -> Constituency, MP -> Constituency).
    Checks if a child entity maps to multiple parents (e.g. one Constituency in multiple States).
    """
    if parent_col not in df.columns or child_col not in df.columns:
        return None

    valid_df = df[[parent_col, child_col]].dropna().astype(str)
    if valid_df.empty:
        return None

    children_per_parent = valid_df.groupby(parent_col)[child_col].nunique()
    parents_per_child = valid_df.groupby(child_col)[parent_col].nunique()

    conflicting_children = parents_per_child[parents_per_child > 1]
    anomalies = []

    for child_val, p_count in conflicting_children.items():
        associated_parents = valid_df[valid_df[child_col] == child_val][parent_col].unique().tolist()
        anomalies.append({
            "entity": child_val,
            "associated_parents_count": p_count,
            "conflicting_parents": associated_parents
        })

    return {
        "parent_column": parent_col,
        "child_column": child_col,
        "total_parent_entities": int(len(children_per_parent)),
        "total_child_entities": int(len(parents_per_child)),
        "conflicting_child_entities_count": int(len(conflicting_children)),
        "relationship_anomaly": anomalies[:10]
    }

def run_relationship_checks(df: pd.DataFrame) -> dict:
    """
    Dynamically identifies entity columns in dataset and profiles hierarchical relationships.
    """
    state_col = find_column_by_keyword(df, ['state'])
    const_col = find_column_by_keyword(df, ['constituency'])
    dist_col = find_column_by_keyword(df, ['district'])
    mp_col = find_column_by_keyword(df, ['mp', 'member of parliament', 'parliamentarian'])
    work_id_col = find_column_by_keyword(df, ['work id', 'work_id', 'work code'])

    relationship_results = {}

    if state_col and const_col:
        res = profile_hierarchical_relationship(df, state_col, const_col)
        if res:
            relationship_results[f"{state_col} -> {const_col}"] = res

    if state_col and dist_col:
        res = profile_hierarchical_relationship(df, state_col, dist_col)
        if res:
            relationship_results[f"{state_col} -> {dist_col}"] = res

    if mp_col and const_col:
        res = profile_hierarchical_relationship(df, mp_col, const_col)
        if res:
            relationship_results[f"{mp_col} -> {const_col}"] = res

    if work_id_col and state_col:
        res = profile_hierarchical_relationship(df, work_id_col, state_col)
        if res:
            relationship_results[f"{work_id_col} -> {state_col}"] = res

    return relationship_results
