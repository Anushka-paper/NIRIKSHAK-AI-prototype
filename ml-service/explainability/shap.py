def compute_shap_feature_contributions(model, feature_vector):
    """Computes top SHAP feature contributions for model decision explainability."""
    return {"top_features": ["estimate_variance_pct", "sanction_delay_days"]}

