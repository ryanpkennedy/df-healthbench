"""
Health check endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict

from app.database import get_db, check_db_connection

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.
    
    Returns:
        Dictionary with status confirmation
        
    Example:
        >>> GET /health
        >>> {"status": "ok"}
    """
    return {"status": "ok"}


@router.get("/health/db")
async def health_check_with_db(db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Health check endpoint with database connectivity check. Verifies both the application and database are accessible.
    
    Args:
        db: Database session (injected)
        
    Returns:
        Dictionary with status and database connection status
        
    Example:
        >>> GET /health/db
        >>> {"status": "ok", "database": "connected"}
    """
    try:
        result = db.execute(text("SELECT 1"))
        result.fetchone()  # Actually fetch the result to ensure connection works
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "ok",
        "database": db_status
    }

