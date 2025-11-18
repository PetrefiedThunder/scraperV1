"""
Database session management.

Provides database engine, session factory, and dependency injection.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from grandma_scraper.db.config import get_database_url


# Create database engine
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,  # Check connections before using
    echo=False,  # Set to True for SQL logging
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.

    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()

    Yields:
        Database session that is automatically closed after use
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
