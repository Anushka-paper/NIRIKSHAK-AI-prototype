import numpy as np

def compute_feature_attributions(X_scaled, feature_names):
    attributions = []
    if len(X_scaled) == 0:
        return attributions
        
    for row in X_scaled:
        abs_dev = np.abs(row)
        top_indices = np.argsort(abs_dev)[::-1][:2]
        top_feats = [feature_names[i] for i in top_indices if abs_dev[i] > 0.5]
        attributions.append(", ".join(top_feats) if top_feats else "multivariate_combination")
        
    return attributions
