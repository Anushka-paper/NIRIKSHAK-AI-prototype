def calculate_quality_score(total_rows, error_count, warning_count):
    if total_rows == 0:
        return 100.0
    error_penalty = (error_count / total_rows) * 100.0 * 5.0
    warning_penalty = (warning_count / total_rows) * 100.0 * 0.5
    score = 100.0 - (error_penalty + warning_penalty)
    return max(0.0, min(100.0, round(score, 2)))
