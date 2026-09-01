import csv
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from core.config import settings
from db.models import (
    Base,
    Expenditure,
    Geography,
    IDAMaster,
    MPMaster,
    VendorMaster,
    WorkCompleted,
    WorkRecommended,
    WorkSanctioned,
)
from db.session import engine


ROOT_DIR = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT_DIR / "data" / "synthetic" / "raw_csvs"


def _empty_to_none(value: str | None):
    return None if value == "" else value


def _coerce_boolean_value(key: str, value: str | None):
    value = _empty_to_none(value)
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if key.lower().startswith(("has_", "is_", "was_", "did_")) and normalized in {"true", "false", "yes", "no", "y", "n", "1", "0"}:
        return normalized in {"true", "yes", "y", "1"}
    if normalized in {"true", "false", "yes", "no", "y", "n", "1", "0"}:
        return normalized in {"true", "yes", "y", "1"}
    return value


def _coerce_datetime_value(key: str, value: str | None):
    value = _empty_to_none(value)
    if value is None:
        return None
    try:
        if "date" in key.lower() or "created_at" in key.lower():
            if "T" in value:
                return datetime.fromisoformat(value)
            return date.fromisoformat(value)
    except ValueError:
        pass
    return _coerce_boolean_value(key, value)


def _read_csv(file_name: str):
    with (RAW_DIR / file_name).open(newline="", encoding="utf-8") as handle:
        rows = []
        for row in csv.DictReader(handle):
            normalized = {}
            for key, value in row.items():
                normalized[key] = _coerce_datetime_value(key, value)
            rows.append(normalized)
        return rows


def ensure_demo_database() -> None:
    if not settings.auto_seed_sqlite or "sqlite" not in settings.database_url:
        return

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    if "works_recommended" in inspector.get_table_names():
        with Session(engine) as session:
            if session.query(WorkRecommended).first():
                return

    if not RAW_DIR.exists():
        return

    load_order = [
        (Geography, "Geography.csv"),
        (MPMaster, "MP_Master.csv"),
        (VendorMaster, "Vendor_Master.csv"),
        (IDAMaster, "IDA_Master.csv"),
        (WorkRecommended, "Works_Recommended.csv"),
        (WorkSanctioned, "Works_Sanctioned.csv"),
        (Expenditure, "Expenditure.csv"),
        (WorkCompleted, "Works_Completed.csv"),
    ]

    with Session(engine) as session:
        for model, file_name in load_order:
            rows = _read_csv(file_name)
            if rows:
                session.bulk_insert_mappings(model, rows)
        session.commit()
