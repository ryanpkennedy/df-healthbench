"""
Service layer for document operations.

This module contains business logic for document management.
Services coordinate between routes and CRUD operations, handling
validation, error handling, and complex workflows.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict, Any
import logging

from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentResponse, DocumentListResponse
from app.crud import document as document_crud
from app.crud import document_summary as summary_crud


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
    def update_document(
        db: Session,
        document_id: int,
        document_data: DocumentUpdate
    ) -> DocumentResponse:
        """
        Update an existing document.

        Args:
            db: Database session
            document_id: ID of document to update
            document_data: DocumentUpdate schema with optional title/content

        Returns:
            DocumentResponse with updated document data

        Raises:
            DocumentNotFoundError: If document doesn't exist
            SQLAlchemyError: If database operation fails

        Example:
            >>> doc_data = DocumentUpdate(title="Updated Title")
            >>> response = DocumentService.update_document(db, 1, doc_data)
            >>> print(f"Updated document: {response.title}")
        """
        try:
            logger.info(f"Updating document with ID: {document_id}")

            updated_doc = document_crud.update_document(
                db,
                document_id,
                title=document_data.title,
                content=document_data.content
            )

            if not updated_doc:
                logger.warning(f"Document with ID {document_id} not found for update")
                raise DocumentNotFoundError(f"Document with ID {document_id} not found")

            logger.info(f"Successfully updated document: {document_id}")
            return DocumentResponse.model_validate(updated_doc)

        except DocumentNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error while updating document {document_id}: {e}")
            db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error while updating document {document_id}: {e}")
            db.rollback()
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
    
    @staticmethod
    def check_summary_cache(db: Session, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Check if a valid cached summary exists for a document.
        
        A cached summary is valid if it was created/updated AFTER the document's
        last update timestamp, meaning the summary reflects the current document version.
        
        Args:
            db: Database session
            document_id: ID of the document
            
        Returns:
            Dictionary with cached summary data if valid cache exists, None otherwise.
            Returns: {
                "summary_text": str,
                "model_used": str,
                "token_usage": dict,
                "from_cache": True
            }
        """
        try:
            # Fetch document
            document = document_crud.get_document(db, document_id)
            if not document:
                logger.warning(f"Document {document_id} not found for cache check")
                return None
            
            # Fetch cached summary
            cached_summary = summary_crud.get_summary_by_document_id(db, document_id)
            
            if not cached_summary:
                logger.info(f"No cached summary found for document {document_id}")
                return None
            
            # Validate cache freshness: summary.updated_at must be >= document.updated_at
            if cached_summary.updated_at >= document.updated_at:
                logger.info(
                    f"Valid cache found for document {document_id}: "
                    f"summary_updated={cached_summary.updated_at}, "
                    f"document_updated={document.updated_at}"
                )
                return {
                    "summary_text": cached_summary.summary_text,
                    "model_used": cached_summary.model_used,
                    "token_usage": cached_summary.token_usage or {},
                    "from_cache": True
                }
            else:
                logger.info(
                    f"Stale cache found for document {document_id}: "
                    f"summary_updated={cached_summary.updated_at}, "
                    f"document_updated={document.updated_at} - will regenerate"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error checking summary cache for document {document_id}: {e}")
            return None
    
    @staticmethod
    def save_summary_cache(
        db: Session,
        document_id: int,
        summary_text: str,
        model_used: str,
        token_usage: Dict[str, Any]
    ) -> bool:
        """
        Save or update a summary in the cache.
        
        Args:
            db: Database session
            document_id: ID of the document
            summary_text: Generated summary text
            model_used: LLM model used
            token_usage: Token usage statistics
            
        Returns:
            True if successfully saved, False otherwise
        """
        try:
            logger.info(f"Saving summary cache for document {document_id}")
            
            summary_crud.create_or_update_summary(
                db=db,
                document_id=document_id,
                summary_text=summary_text,
                model_used=model_used,
                token_usage=token_usage
            )
            
            logger.info(f"Successfully saved summary cache for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving summary cache for document {document_id}: {e}")
            return False

