"""
Service layer for document operations.

This module contains business logic for document management.
Services coordinate between routes and CRUD operations, handling
validation, error handling, and complex workflows.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
import logging

from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentListResponse
from app.crud import document as document_crud


logger = logging.getLogger(__name__)


class DocumentNotFoundError(Exception):
    """Raised when a document is not found in the database."""
    pass


class DocumentService:
    """
    Service class for document operations.
    
    This class encapsulates business logic for document management,
    providing a clean interface for route handlers.
    """
    
    @staticmethod
    def get_all_document_ids(db: Session) -> DocumentListResponse:
        """
        Retrieve all document IDs.
            
        Returns:
            DocumentListResponse with list of IDs and count
        """
        try:
            logger.info("Fetching all document IDs")
            document_ids = document_crud.get_document_ids(db)
            
            logger.info(f"Successfully retrieved {len(document_ids)} document IDs")
            
            return DocumentListResponse(
                document_ids=document_ids,
                count=len(document_ids)
            )
            
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching document IDs: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching document IDs: {e}")
            raise
    
    @staticmethod
    def create_new_document(db: Session, document_data: DocumentCreate) -> DocumentResponse:
        """
        Create a new document.
        
        Args:
            db: Database session
            document_data: DocumentCreate schema with title and content
            
        Returns:
            DocumentResponse with created document data
            
        Raises:
            SQLAlchemyError: If database operation fails
            ValueError: If validation fails
            
        Example:
            >>> doc_data = DocumentCreate(title="Test", content="Test content...")
            >>> response = DocumentService.create_new_document(db, doc_data)
            >>> print(f"Created document ID: {response.id}")
        """
        try:
            logger.info(f"Creating new document: {document_data.title}")
            
            # Additional business logic can go here
            # For example: check for duplicate titles, sanitize content, etc.
            
            # Create document via CRUD layer
            document = document_crud.create_document(db, document_data)
            
            logger.info(f"Successfully created document with ID: {document.id}")
            
            # Convert SQLAlchemy model to Pydantic schema
            return DocumentResponse.model_validate(document)
            
        except SQLAlchemyError as e:
            logger.error(f"Database error while creating document: {e}")
            db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error while creating document: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_document_by_id(db: Session, document_id: int) -> DocumentResponse:
        """
        Retrieve a document by ID.
        
        Args:
            db: Database session
            document_id: ID of document to retrieve
            
        Returns:
            DocumentResponse with document data
            
        Raises:
            DocumentNotFoundError: If document doesn't exist
            SQLAlchemyError: If database operation fails
            
        Example:
            >>> try:
            ...     response = DocumentService.get_document_by_id(db, 1)
            ...     print(response.title)
            ... except DocumentNotFoundError:
            ...     print("Document not found")
        """
        try:
            logger.info(f"Fetching document with ID: {document_id}")
            
            document = document_crud.get_document(db, document_id)
            
            if not document:
                logger.warning(f"Document with ID {document_id} not found")
                raise DocumentNotFoundError(f"Document with ID {document_id} not found")
            
            logger.info(f"Successfully retrieved document: {document.title}")
            
            return DocumentResponse.model_validate(document)
            
        except DocumentNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching document {document_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching document {document_id}: {e}")
            raise
    
    @staticmethod
    def get_all_documents(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[DocumentResponse]:
        """
        Retrieve all documents with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of DocumentResponse objects
            
        Raises:
            SQLAlchemyError: If database operation fails
            
        Example:
            >>> documents = DocumentService.get_all_documents(db, skip=0, limit=10)
            >>> for doc in documents:
            ...     print(doc.title)
        """
        try:
            logger.info(f"Fetching documents (skip={skip}, limit={limit})")
            
            documents = document_crud.get_documents(db, skip=skip, limit=limit)
            
            logger.info(f"Successfully retrieved {len(documents)} documents")
            
            # Convert list of SQLAlchemy models to Pydantic schemas
            return [DocumentResponse.model_validate(doc) for doc in documents]
            
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching documents: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching documents: {e}")
            raise
    
    @staticmethod
    def delete_document(db: Session, document_id: int) -> bool:
        """
        Delete a document by ID.
        
        Args:
            db: Database session
            document_id: ID of document to delete
            
        Returns:
            True if document was deleted
            
        Raises:
            DocumentNotFoundError: If document doesn't exist
            SQLAlchemyError: If database operation fails
        """
        try:
            logger.info(f"Deleting document with ID: {document_id}")
            
            success = document_crud.delete_document(db, document_id)
            
            if not success:
                logger.warning(f"Document with ID {document_id} not found for deletion")
                raise DocumentNotFoundError(f"Document with ID {document_id} not found")
            
            logger.info(f"Successfully deleted document with ID: {document_id}")
            
            return True
            
        except DocumentNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting document {document_id}: {e}")
            db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error while deleting document {document_id}: {e}")
            db.rollback()
            raise

