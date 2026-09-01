from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from db.models import MPMaster, MPAlias

def resolve_mp(db: Session, raw_name: str, state_id: int = None) -> tuple[int | None, float]:
    """
    Resolves a raw MP name to a canonical mp_id using fuzzy matching.
    If state_id is provided, scopes the search to that state.
    """
    if not raw_name or not str(raw_name).strip():
        return None, 0.0
        
    s_raw = str(raw_name).strip().lower()
    
    # Check alias table first
    aliases = db.query(MPAlias).all()
    for alias in aliases:
        if alias.raw_name.lower() == s_raw:
            # We assume alias is confirmed if it's in this table
            return alias.mp_id, 1.0
            
    # Fuzzy match against master table
    query = db.query(MPMaster)
    if state_id:
        query = query.filter(MPMaster.state_id == state_id)
        
    masters = query.all()
    best_match = None
    best_score = 0.0
    
    for m in masters:
        score = SequenceMatcher(None, s_raw, m.canonical_name.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = m.mp_id
            
    if best_score >= 0.95:
        return best_match, best_score
    elif best_score >= 0.80:
        return None, best_score # Queue for human review
    else:
        return None, best_score
