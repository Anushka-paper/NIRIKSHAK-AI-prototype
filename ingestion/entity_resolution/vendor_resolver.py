from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from db.models import VendorMaster, VendorAlias

def resolve_vendor(db: Session, raw_name: str) -> tuple[int | None, float]:
    """
    Resolves a raw vendor name to a canonical vendor_id using fuzzy matching.
    Returns (vendor_id, confidence_score).
    If confidence is < 0.80, returns (None, score) for quarantine/human review.
    """
    if not raw_name or not str(raw_name).strip():
        return None, 0.0
        
    s_raw = str(raw_name).strip().lower()
    
    # Check exact match in alias table first (O(1))
    # We load everything into memory for this simple implementation, 
    # but in a real system we might use pg_trgm for indexed similarity search
    aliases = db.query(VendorAlias).all()
    for alias in aliases:
        if alias.raw_name.lower() == s_raw:
            return alias.vendor_id, 1.0
            
    # Fuzzy match against master table
    masters = db.query(VendorMaster).all()
    best_match = None
    best_score = 0.0
    
    for m in masters:
        score = SequenceMatcher(None, s_raw, m.canonical_name.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = m.vendor_id
            
    if best_score >= 0.95:
        # High confidence auto-resolve
        return best_match, best_score
    elif best_score >= 0.80:
        # Medium confidence, return it but it should technically be queued.
        # Per spec: "80-95% similarity routed to a human-confirmation queue rather than auto-merged"
        # We return it as unresolved (None) with the score so the caller can queue it
        return None, best_score
    else:
        # Low confidence, no match
        return None, best_score
