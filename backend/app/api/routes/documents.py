"""
Document management endpoints. Provides CRUD operations for medical documents.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentListResponse,
    DocumentDeleteResponse
)
from app.services.document import DocumentService, DocumentNotFoundError
from datetime import datetime

router = APIRouter()

@router.get("", response_model=DocumentListResponse)
async def get_documents(db: Session = Depends(get_db)) -> DocumentListResponse:
    """
    Get all document IDs.
    
    Returns a list of all document IDs in the database.
    This is an optimized query that only fetches IDs.
    
    Args:
        db: Database session (injected)
        
    Returns:
        DocumentListResponse with list of IDs and count
    """
    try:
        return DocumentService.get_all_document_ids(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.post(
    "/",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """
    Create a new document with the provided title and content.
    
    Args:
        document: DocumentCreate schema with title and content
        db: Database session (injected)
        
    Returns:
        DocumentResponse with created document data including ID and timestamps
    """
    try:
        return DocumentService.create_new_document(db, document)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """
    Get a document by ID.
    
    Retrieves a single document with all its details.
    
    Args:
        document_id: ID of the document to retrieve
        db: Database session (injected)
        
    Returns:
        DocumentResponse with full document data
        
    Raises:
        HTTPException: 404 if document not found
        HTTPException: 500 if database error occurs
    """
    try:
        return DocumentService.get_document_by_id(db, document_id)
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.get("/list/all", response_model=List[DocumentResponse])
async def get_all_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[DocumentResponse]:
    """
    Get all documents with full details (paginated).
    
    Retrieves all documents with pagination support.
    Use this endpoint when you need full document data, not just IDs.
    
    Args:
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100)
        db: Database session (injected)
        
    Returns:
        List of DocumentResponse objects
    """
    try:
        return DocumentService.get_all_documents(db, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a document by ID.
    
    Permanently deletes a document from the database.
    
    Args:
        document_id: ID of the document to delete
        db: Database session (injected)
        
    Returns:
        None (204 No Content)
    """
    try:
        DocumentService.delete_document(db, document_id)

        return DocumentDeleteResponse(
            success=True,
            message=f"Document {document_id} deleted successfully",
            document_id=document_id,
            deleted_at=datetime.now()
        )

    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

