from sqlalchemy import create_engine
from db.models import Base
import os

DATABASE_URL = "sqlite:///./nirikshak.db"

def init_db():
    print(f"Initializing SQLite database at {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)
    
    # Create all tables defined in models.py
    Base.metadata.create_all(engine)
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
