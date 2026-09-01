from data_pipeline.entity_resolution.similarity import compute_string_similarity

def compute_composite_score(name_sim, location_match=False, house_match=False, context_match=False):
    score = name_sim * 0.50
    if location_match:
        score += 0.25
    if house_match:
        score += 0.15
    if context_match:
        score += 0.10
    return round(min(1.0, score), 4)
