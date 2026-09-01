from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from db.models import Geography, GeoLevel

def resolve_geography(db: Session, raw_name: str, level: GeoLevel, parent_id: int = None) -> tuple[int | None, float]:
    """
    Resolves a raw state or constituency name to a canonical geo_id using fuzzy matching.
    """
    if not raw_name or not str(raw_name).strip():
        return None, 0.0
        
    s_raw = str(raw_name).strip().lower()
    
    query = db.query(Geography).filter(Geography.level == level)
    if parent_id:
        query = query.filter(Geography.parent_geo_id == parent_id)
        
    geos = query.all()
    best_match = None
    best_score = 0.0
    
    for g in geos:
        score = SequenceMatcher(None, s_raw, g.name.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = g.geo_id
            
    if best_score >= 0.90:
        return best_match, best_score
    else:
        return None, best_score
