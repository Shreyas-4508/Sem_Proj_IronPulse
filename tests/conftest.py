"""
Pytest configuration for IronPulse tests.
Sets up an in-memory SQLite test database that is isolated per test function.
"""

import sys
import os
import pytest

# Ensure the project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Point to in-memory SQLite for all tests (overrides DATABASE_URL)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["BCRYPT_ROUNDS"] = "4"  # Faster hashing for tests

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from database.base import Base
import models.user    # noqa: F401 — register models
import models.profile # noqa: F401
import models.exercise # noqa: F401
import models.workout # noqa: F401
import models.nutrition # noqa: F401
import models.gamification # noqa: F401


@pytest.fixture(scope="function")
def db_engine():
    """Creates a fresh in-memory SQLite engine for each test function."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    # Enable foreign keys in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db(db_engine):
    """Provides a database session that rolls back after each test."""
    Session = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
    session = Session()
    try:
        yield session
        session.rollback()
    finally:
        session.close()
