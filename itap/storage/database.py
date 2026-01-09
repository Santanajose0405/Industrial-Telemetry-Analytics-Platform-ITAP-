"""
Database configuration and session management.

SQLite is used for local development.
We support overriding the DB URL for tests so they can run in isolation.
"""

from __future__ import annotations

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DEFAULT_DB_PATH = Path("data") / "telemetry.db"

def make_engine(db_url: str | None = None):
    """
    Create a SQLAlchemy engine.

    If db_url is None, use the default SQLite path under /data.
    """
    if db_url is None:
        db_url = f"sqlite:///{DEFAULT_DB_PATH}"
    return create_engine(db_url, future=True, echo=False)  

ENGINE = make_engine()
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False)