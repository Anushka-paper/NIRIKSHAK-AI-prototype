def validate_schema(df, required_columns):
    """Validates dataframe schema integrity."""
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return True

