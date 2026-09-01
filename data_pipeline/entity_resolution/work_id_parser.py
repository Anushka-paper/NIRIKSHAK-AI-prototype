import re

def parse_work_id(raw_work_id):
    if not isinstance(raw_work_id, str) or not raw_work_id.strip():
        return {
            "source_work_id": "",
            "is_esakshi": False,
            "house": None,
            "mp_code": None,
            "financial_year": None,
            "sequence": None
        }

    s = raw_work_id.strip()
    match = re.match(r'^(WS)/([A-Z0-9]+)/(\d{4}-\d{4})/(\d+)$', s)
    if match:
        prefix, mp_tag, fy, seq = match.groups()
        house = "LOK_SABHA" if "MP" in mp_tag else "RAJYA_SABHA"
        return {
            "source_work_id": s,
            "is_esakshi": True,
            "house": house,
            "mp_code": mp_tag,
            "financial_year": fy,
            "sequence": seq
        }
        
    return {
        "source_work_id": s,
        "is_esakshi": False,
        "house": None,
        "mp_code": None,
        "financial_year": None,
        "sequence": None
    }
