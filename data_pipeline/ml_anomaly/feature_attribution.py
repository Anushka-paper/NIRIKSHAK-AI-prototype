import numpy as np

def compute_feature_attributions(X_scaled, feature_names):
    """
    Computes vectorized per-feature deviation attributions (§8, Question 10).
    """
    if len(X_scaled) == 0:
        return []

    abs_dev = np.abs(X_scaled)
    # Vectorized top 2 feature indices selection
    top2_idx = np.argsort(abs_dev, axis=1)[:, ::-1][:, :2]

    feat_names_arr = np.array(feature_names)
    attributions = []
    for r in range(len(X_scaled)):
        row_dev = abs_dev[r]
        row_idx = top2_idx[r]
        valid_feats = [feat_names_arr[i] for i in row_idx if row_dev[i] > 0.5]
        attributions.append(", ".join(valid_feats) if valid_feats else "multivariate_combination")

    return attributions
