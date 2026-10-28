"""
Database connection management.
Provides engine creation, session factory, and health checks.
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError

from config import settings

logger = logging.getLogger(__name__)

# Build engine with appropriate settings
_engine_kwargs = {
    "echo": settings.DEBUG and settings.is_development,
    "pool_pre_ping": True,  # Verify connections before use
}

if settings.using_sqlite:
    # SQLite-specific settings
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL connection pool settings
    _engine_kwargs["pool_size"] = 5
    _engine_kwargs["max_overflow"] = 10
    _engine_kwargs["pool_timeout"] = 30

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

# Enable foreign key enforcement for SQLite
if settings.using_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager that provides a database session.
    Automatically commits on success and rolls back on error.

    Usage:
        with get_db_session() as db:
            user = db.query(User).filter_by(id=1).first()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_database_connection() -> tuple[bool, str]:
    """
    Tests whether the database is reachable.
    Returns (success: bool, message: str).
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Database connection successful."
    except OperationalError as exc:
        logger.error("Database connection failed: %s", exc)
        return False, f"Database connection failed: {exc}"
    except Exception as exc:
        logger.error("Unexpected database error: %s", exc)
        return False, f"Unexpected error: {exc}"


def init_db() -> None:
    """
    Creates all tables that do not yet exist.
    Used only for development/testing with SQLite.
    For PostgreSQL production, always use Alembic migrations instead.
    """
    from database.base import Base
    # Import models so they register with Base.metadata
    import models.user        # noqa: F401
    import models.profile     # noqa: F401
    import models.exercise    # noqa: F401
    import models.workout     # noqa: F401
    import models.nutrition    # noqa: F401
    import models.gamification # noqa: F401

    Base.metadata.create_all(bind=engine)
    from services.catalog_service import seed_catalog

    with SessionLocal() as db:
        seed_catalog(db)
        db.commit()
    logger.info("Database tables created (development mode).")
