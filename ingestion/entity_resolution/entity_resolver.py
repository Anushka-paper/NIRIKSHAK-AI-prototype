import os
import sys
import re
from difflib import SequenceMatcher

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "backend/app"))

from backend.app.db.session import SessionLocal
from backend.app.db.models import MPMaster, MPAlias, VendorMaster, VendorAlias, WorkRecommended, WorkSanctioned, Expenditure
from ingestion.entity_resolution.normalizers import normalize_text
from ingestion.entity_resolution.work_id_parser import parse_work_id

class WorkIDResolver:
    """Canonical Work ID Extractor & Parser."""
    
    @staticmethod
    def parse_canonical_work_id(raw_work_id: str) -> tuple[str, str]:
        """Parses raw composite Work ID string."""
        canonical = parse_work_id(str(raw_work_id))
        return canonical, str(raw_work_id)


class MPNameResolver:
    """MP Entity Resolution & Alias Mapper."""

    @staticmethod
    def normalize_mp_name(name: str) -> str:
        """Strips honorifics and normalizes whitespace."""
        res = normalize_text(name, entity_type="mp")
        return res["normalized_value"].title()

    @classmethod
    def resolve_mp(cls, db_session, raw_name: str) -> tuple[int, str]:
        """Resolves MP raw string to stable mp_id and canonical name."""
        norm_name = cls.normalize_mp_name(raw_name)
        if not norm_name:
            return 1, "Unassigned MP"

        existing = db_session.query(MPMaster).filter(MPMaster.canonical_name == norm_name).first()
        if existing:
            return existing.mp_id, existing.canonical_name

        new_mp = MPMaster(canonical_name=norm_name, house="Lok Sabha")
        db_session.add(new_mp)
        db_session.flush()
        
        alias = MPAlias(mp_id=new_mp.mp_id, raw_name=raw_name, is_confirmed=True)
        db_session.add(alias)
        db_session.flush()

        return new_mp.mp_id, new_mp.canonical_name


class VendorNameResolver:
    """Vendor Entity Resolution & Alias Mapper."""

    @staticmethod
    def normalize_vendor_name(name: str) -> str:
        """Standardizes vendor company suffixes and formatting."""
        res = normalize_text(name, entity_type="vendor")
        return res["normalized_value"].title()

    @classmethod
    def resolve_vendor(cls, db_session, raw_vendor: str) -> tuple[int, str]:
        """Resolves vendor raw string to stable vendor_id and canonical name."""
        norm_name = cls.normalize_vendor_name(raw_vendor)
        if not norm_name:
            return 1, "Unassigned Vendor"

        existing = db_session.query(VendorMaster).filter(VendorMaster.canonical_name == norm_name).first()
        if existing:
            return existing.vendor_id, existing.canonical_name

        new_vendor = VendorMaster(canonical_name=norm_name)
        db_session.add(new_vendor)
        db_session.flush()

        alias = VendorAlias(vendor_id=new_vendor.vendor_id, raw_name=raw_vendor, match_confidence=1.0)
        db_session.add(alias)
        db_session.flush()

        return new_vendor.vendor_id, new_vendor.canonical_name


def run_entity_resolution_pipeline():
    """Runs Entity Resolution across all DB entities."""
    from ingestion.entity_resolution.pipeline import run_entity_resolution_pipeline as run_pipeline
    return run_pipeline()

if __name__ == "__main__":
    run_entity_resolution_pipeline()

