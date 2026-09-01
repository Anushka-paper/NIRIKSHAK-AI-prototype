def clean_encoding(val):
    if not isinstance(val, str):
        return val
    if val.startswith('\ufeff'):
        val = val.lstrip('\ufeff')
    val = val.replace('\xa0', ' ')
    val = val.replace('–', '-').replace('é', 'e')
    return val
