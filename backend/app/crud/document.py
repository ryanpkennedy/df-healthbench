"""
CRUD operations for Document model.

This module contains all database query operations for documents.
These functions should be database-only - no business logic.
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.document import Document
from app.schemas.document import DocumentCreate


def get_document(db: Session, document_id: int) -> Optional[Document]:
    """
    Retrieve a single document by ID.
    
    Args:
        db: Database session
        document_id: ID of the document to retrieve
        
    Returns:
        Document model instance if found, None otherwise
    """
    return db.query(Document).filter(Document.id == document_id).first()


def get_documents(db: Session, skip: int = 0, limit: int = 100) -> List[Document]:
    """
    Retrieve all documents with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
    Returns:
        List of Document model instances
    """
    return db.query(Document).offset(skip).limit(limit).all()


def get_document_ids(db: Session) -> List[int]:
    """
    Retrieve all document IDs only (optimized query).
    
    This is more efficient than fetching full document objects
    when only IDs are needed.
    
    Args:
        db: Database session
        
    Returns:
        List of document IDs
    """
    # Query only the id column for efficiency
    results = db.query(Document.id).all()
    # Extract IDs from tuples [(1,), (2,), (3,)] -> [1, 2, 3]
    return [row[0] for row in results]


def create_document(db: Session, document: DocumentCreate) -> Document:
    """
    Create a new document in the database.
    
    Args:
        db: Database session
        document: DocumentCreate schema with title and content
        
    Returns:
        Created Document model instance with ID and timestamps
        
    Raises:
        SQLAlchemyError: If database operation fails
        
    Example:
        >>> doc_data = DocumentCreate(title="Test", content="Test content")
        >>> new_doc = create_document(db, doc_data)
        >>> print(f"Created document with ID: {new_doc.id}")
    """
    # Create SQLAlchemy model from Pydantic schema
    db_document = Document(
        title=document.title,
        content=document.content
    )
    
    # Add to session and commit
    db.add(db_document)
    db.commit()
    
    # Refresh to get generated values (id, timestamps)
    db.refresh(db_document)
    
    return db_document


def update_document(
    db: Session,
    document_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None
) -> Optional[Document]:
    """
    Update an existing document.
    
    Args:
        db: Database session
        document_id: ID of document to update
        title: New title (optional)
        content: New content (optional)
        
    Returns:
        Updated Document model instance if found, None otherwise
        
    Example:
        >>> updated_doc = update_document(db, 1, title="New Title")
        >>> if updated_doc:
        ...     print(f"Updated: {updated_doc.title}")
    """
    document = get_document(db, document_id)
    
    if not document:
        return None
    
    # Update fields if provided
    if title is not None:
        document.title = title
    if content is not None:
        document.content = content
    
    db.commit()
    db.refresh(document)
    
    return document


def delete_document(db: Session, document_id: int) -> bool:
    """
    Delete a document by ID.
    
    Args:
        db: Database session
        document_id: ID of document to delete
        
    Returns:
        True if document was deleted, False if not found
        
    Example:
        >>> success = delete_document(db, 1)
        >>> if success:
        ...     print("Document deleted")
    """
    document = get_document(db, document_id)
    
    if not document:
        return False
    
    db.delete(document)
    db.commit()
    
    return True


def get_documents_count(db: Session) -> int:
    """
    Get total count of documents in database.
    
    Args:
        db: Database session
        
    Returns:
        Total number of documents
        
    Example:
        >>> count = get_documents_count(db)
        >>> print(f"Total documents: {count}")
    """
    return db.query(Document).count()

