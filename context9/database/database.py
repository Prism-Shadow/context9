"""Database connection and session management."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from loguru import logger

# Database file path
DB_PATH = os.getenv("CONTEXT9_DB_PATH", "context9.db")
DATABASE_URL = f"sqlite:///{DB_PATH}?check_same_thread=False"

# NullPool: each request gets its own connection (no sharing). Required for SQLite
# when sync code runs in FastAPI's thread pool; StaticPool's single connection
# would be used from multiple threads and trigger sqlite3.InterfaceError.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
    echo=False,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from .models import Base

    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized at {DB_PATH}")
