from data_pipeline.cleaning.encoding import clean_encoding

def clean_whitespace(val):
    if not isinstance(val, str):
        return val
    cleaned = clean_encoding(val)
    cleaned = cleaned.strip()
    cleaned = ' '.join(cleaned.split())
    return cleaned
