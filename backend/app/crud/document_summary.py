"""
CRUD operations for DocumentSummary model.

This module contains all database query operations for document summaries.
Handles caching logic for LLM-generated summaries.
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.models.document_summary import DocumentSummary


def get_summary_by_document_id(db: Session, document_id: int) -> Optional[DocumentSummary]:
    """
    Retrieve a cached summary for a specific document.
    
    Args:
        db: Database session
        document_id: ID of the document
        
    Returns:
        DocumentSummary model instance if found, None otherwise
    """
    return db.query(DocumentSummary).filter(DocumentSummary.document_id == document_id).first()


def create_summary(
    db: Session,
    document_id: int,
    summary_text: str,
    model_used: Optional[str] = None,
    token_usage: Optional[Dict[str, Any]] = None
) -> DocumentSummary:
    """
    Create a new document summary in the database.
    
    Args:
        db: Database session
        document_id: ID of the document being summarized
        summary_text: LLM-generated summary text
        model_used: Name of the LLM model used
        token_usage: Token usage statistics dictionary
        
    Returns:
        Created DocumentSummary model instance
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    db_summary = DocumentSummary(
        document_id=document_id,
        summary_text=summary_text,
        model_used=model_used,
        token_usage=token_usage
    )
    
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    
    return db_summary


def update_summary(
    db: Session,
    document_id: int,
    summary_text: str,
    model_used: Optional[str] = None,
    token_usage: Optional[Dict[str, Any]] = None
) -> Optional[DocumentSummary]:
    """
    Update an existing document summary.
    
    Args:
        db: Database session
        document_id: ID of the document
        summary_text: New summary text
        model_used: Name of the LLM model used
        token_usage: Token usage statistics dictionary
        
    Returns:
        Updated DocumentSummary model instance if found, None otherwise
    """
    summary = get_summary_by_document_id(db, document_id)
    
    if not summary:
        return None
    
    # Update fields
    summary.summary_text = summary_text
    summary.model_used = model_used
    summary.token_usage = token_usage
    
    db.commit()
    db.refresh(summary)
    
    return summary


def create_or_update_summary(
    db: Session,
    document_id: int,
    summary_text: str,
    model_used: Optional[str] = None,
    token_usage: Optional[Dict[str, Any]] = None
) -> DocumentSummary:
    """
    Create or update a document summary (upsert operation).
    
    If a summary already exists for the document, update it.
    Otherwise, create a new summary.
    
    Args:
        db: Database session
        document_id: ID of the document being summarized
        summary_text: LLM-generated summary text
        model_used: Name of the LLM model used
        token_usage: Token usage statistics dictionary
        
    Returns:
        DocumentSummary model instance (created or updated)
        
    Example:
        >>> summary = create_or_update_summary(
        ...     db, 
        ...     document_id=1, 
        ...     summary_text="Patient presents with...",
        ...     model_used="gpt-4o-mini",
        ...     token_usage={"total": 230}
        ... )
    """
    existing_summary = get_summary_by_document_id(db, document_id)
    
    if existing_summary:
        return update_summary(db, document_id, summary_text, model_used, token_usage)
    else:
        return create_summary(db, document_id, summary_text, model_used, token_usage)


def delete_summary(db: Session, document_id: int) -> bool:
    """
    Delete a cached summary for a document.
    
    Args:
        db: Database session
        document_id: ID of the document
        
    Returns:
        True if summary was deleted, False if not found
        
    Example:
        >>> success = delete_summary(db, 1)
        >>> if success:
        ...     print("Cache cleared for document")
    """
    summary = get_summary_by_document_id(db, document_id)
    
    if not summary:
        return False
    
    db.delete(summary)
    db.commit()
    
    return True

