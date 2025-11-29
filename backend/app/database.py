"""
Database connection and session management module.

This module sets up SQLAlchemy engine, session factory, and provides
dependency injection for FastAPI routes.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,         # Maximum number of connections to keep open
    max_overflow=10,     # Maximum number of connections to create beyond pool_size
    echo=False           # Set to True to log all SQL statements (useful for debugging)
)

# Create SessionLocal factory for database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for declarative models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that provides a database session.
    
    This function is used with FastAPI's Depends() to inject a database
    session into route handlers. It ensures the session is properly closed
    after the request is completed.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """
    Create all database tables defined in models.
    
    This function should be called on application startup to ensure
    all tables exist. It's idempotent - safe to call multiple times.
    """
    # Import all models here to ensure they are registered with SQLAlchemy
    # before creating tables
    from app.models import Document, DocumentEmbedding  # noqa: F401
    
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def check_db_connection() -> bool:
    """
    Check if the database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

