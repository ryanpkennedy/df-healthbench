"""
Test CRUD and Service Layer Operations

Tests for:
- CRUD operations (database layer)
- Service layer business logic
- Error handling
- Multiple document operations
"""

import pytest

from app.crud import document as document_crud
from app.schemas.document import DocumentCreate
from app.services.document import DocumentService, DocumentNotFoundError


# ============================================================================
# CRUD Layer Tests
# ============================================================================

class TestCRUDOperations:
    """Test CRUD operations at the database layer."""
    
    @pytest.mark.integration
    def test_create_document(self, db_session):
        """Test creating a document via CRUD layer."""
        doc_data = DocumentCreate(
            title="Test SOAP Note #1",
            content="Subjective: Patient reports headache and fever for 2 days."
        )
        doc = document_crud.create_document(db_session, doc_data)
        
        assert doc.id is not None
        assert doc.title == doc_data.title
        assert doc.content == doc_data.content
        assert doc.created_at is not None
    
    @pytest.mark.integration
    def test_get_document_by_id(self, db_session, sample_document):
        """Test retrieving a document by ID via CRUD layer."""
        retrieved_doc = document_crud.get_document(db_session, sample_document.id)
        
        assert retrieved_doc is not None
        assert retrieved_doc.id == sample_document.id
        assert retrieved_doc.title == sample_document.title
    
    @pytest.mark.integration
    def test_get_document_not_found(self, db_session):
        """Test get_document returns None for non-existent ID."""
        doc = document_crud.get_document(db_session, 999999)
        
        assert doc is None
    
    @pytest.mark.integration
    def test_get_document_ids(self, db_session, sample_document):
        """Test retrieving all document IDs."""
        ids = document_crud.get_document_ids(db_session)
        
        assert isinstance(ids, list)
        assert sample_document.id in ids
    
    @pytest.mark.integration
    def test_get_documents_pagination(self, db_session, sample_document):
        """Test retrieving documents with pagination."""
        docs = document_crud.get_documents(db_session, skip=0, limit=10)
        
        assert isinstance(docs, list)
        assert len(docs) > 0
        assert any(doc.id == sample_document.id for doc in docs)
    
    @pytest.mark.integration
    def test_get_documents_count(self, db_session, sample_document):
        """Test getting total document count."""
        count = document_crud.get_documents_count(db_session)
        
        assert isinstance(count, int)
        assert count > 0
    
    @pytest.mark.integration
    def test_update_document(self, db_session, sample_document):
        """Test updating a document via CRUD layer."""
        new_title = "Updated Test SOAP Note"
        updated_doc = document_crud.update_document(
            db_session,
            sample_document.id,
            title=new_title
        )
        
        assert updated_doc is not None
        assert updated_doc.id == sample_document.id
        assert updated_doc.title == new_title
        assert updated_doc.updated_at > updated_doc.created_at
    
    @pytest.mark.integration
    def test_update_document_not_found(self, db_session):
        """Test update_document returns None for non-existent ID."""
        updated_doc = document_crud.update_document(
            db_session,
            999999,
            title="New Title"
        )
        
        assert updated_doc is None
    
    @pytest.mark.integration
    def test_delete_document(self, db_session, sample_document):
        """Test deleting a document via CRUD layer."""
        doc_id = sample_document.id
        success = document_crud.delete_document(db_session, doc_id)
        
        assert success is True
        
        # Verify deletion
        deleted_doc = document_crud.get_document(db_session, doc_id)
        assert deleted_doc is None
    
    @pytest.mark.integration
    def test_delete_document_not_found(self, db_session):
        """Test delete_document returns False for non-existent ID."""
        success = document_crud.delete_document(db_session, 999999)
        
        assert success is False


# ============================================================================
# Service Layer Tests
# ============================================================================

class TestDocumentService:
    """Test DocumentService business logic layer."""
    
    @pytest.mark.integration
    def test_create_new_document(self, db_session):
        """Test creating a document via service layer."""
        doc_data = DocumentCreate(
            title="Service Test SOAP Note",
            content="Subjective: Patient reports chest pain and shortness of breath."
        )
        response = DocumentService.create_new_document(db_session, doc_data)
        
        assert response.id is not None
        assert response.title == doc_data.title
        assert response.content == doc_data.content
    
    @pytest.mark.integration
    def test_get_document_by_id(self, db_session, sample_document):
        """Test retrieving a document by ID via service layer."""
        response = DocumentService.get_document_by_id(db_session, sample_document.id)
        
        assert response.id == sample_document.id
        assert response.title == sample_document.title
    
    @pytest.mark.integration
    def test_get_document_by_id_not_found(self, db_session):
        """Test service raises DocumentNotFoundError for non-existent document."""
        with pytest.raises(DocumentNotFoundError) as exc_info:
            DocumentService.get_document_by_id(db_session, 999999)
        
        assert "999999" in str(exc_info.value)
    
    @pytest.mark.integration
    def test_get_all_document_ids(self, db_session, sample_document):
        """Test retrieving all document IDs via service layer."""
        response = DocumentService.get_all_document_ids(db_session)
        
        assert hasattr(response, 'document_ids')
        assert hasattr(response, 'count')
        assert isinstance(response.document_ids, list)
        assert response.count > 0
        assert sample_document.id in response.document_ids
    
    @pytest.mark.integration
    def test_get_all_document_ids_empty(self, clean_database):
        """Test get_all_document_ids with empty database."""
        response = DocumentService.get_all_document_ids(clean_database)
        
        assert response.count == 0
        assert response.document_ids == []
    
    @pytest.mark.integration
    def test_get_all_documents(self, db_session, sample_document):
        """Test retrieving all documents via service layer."""
        documents = DocumentService.get_all_documents(db_session, skip=0, limit=10)
        
        assert isinstance(documents, list)
        assert len(documents) > 0
        assert any(doc.id == sample_document.id for doc in documents)
    
    @pytest.mark.integration
    def test_get_all_documents_pagination(self, db_session):
        """Test pagination in get_all_documents."""
        # Create multiple documents
        for i in range(3):
            doc_data = DocumentCreate(
                title=f"Pagination Test #{i+1}",
                content=f"This is test document number {i+1} for pagination testing."
            )
            DocumentService.create_new_document(db_session, doc_data)
        
        # Test skip parameter
        all_docs = DocumentService.get_all_documents(db_session, skip=0, limit=100)
        skipped_docs = DocumentService.get_all_documents(db_session, skip=1, limit=100)
        
        assert len(skipped_docs) == len(all_docs) - 1
        
        # Test limit parameter
        limited_docs = DocumentService.get_all_documents(db_session, skip=0, limit=1)
        assert len(limited_docs) == 1
    
    @pytest.mark.integration
    def test_delete_document(self, db_session, sample_document):
        """Test deleting a document via service layer."""
        doc_id = sample_document.id
        
        # Delete should not raise error
        DocumentService.delete_document(db_session, doc_id)
        
        # Verify deletion by attempting to retrieve
        with pytest.raises(DocumentNotFoundError):
            DocumentService.get_document_by_id(db_session, doc_id)
    
    @pytest.mark.integration
    def test_delete_document_not_found(self, db_session):
        """Test service raises DocumentNotFoundError when deleting non-existent document."""
        with pytest.raises(DocumentNotFoundError) as exc_info:
            DocumentService.delete_document(db_session, 999999)
        
        assert "999999" in str(exc_info.value)


# ============================================================================
# Multiple Documents Tests
# ============================================================================

class TestMultipleDocuments:
    """Test operations involving multiple documents."""
    
    @pytest.mark.integration
    def test_create_multiple_documents(self, db_session):
        """Test creating multiple documents."""
        created_ids = []
        
        for i in range(1, 6):
            doc_data = DocumentCreate(
                title=f"Batch Test Document #{i}",
                content=f"This is test document number {i} with sufficient content for validation."
            )
            response = DocumentService.create_new_document(db_session, doc_data)
            created_ids.append(response.id)
        
        assert len(created_ids) == 5
        assert len(set(created_ids)) == 5  # All IDs should be unique
        
        # Verify all documents exist
        response = DocumentService.get_all_document_ids(db_session)
        for doc_id in created_ids:
            assert doc_id in response.document_ids
    
    @pytest.mark.integration
    def test_bulk_operations(self, db_session):
        """Test bulk create and delete operations."""
        # Create multiple documents
        created_ids = []
        for i in range(3):
            doc_data = DocumentCreate(
                title=f"Bulk Test #{i+1}",
                content=f"Bulk operation test document {i+1} content."
            )
            response = DocumentService.create_new_document(db_session, doc_data)
            created_ids.append(response.id)
        
        initial_count = DocumentService.get_all_document_ids(db_session).count
        
        # Delete all created documents
        for doc_id in created_ids:
            DocumentService.delete_document(db_session, doc_id)
        
        final_count = DocumentService.get_all_document_ids(db_session).count
        
        assert final_count == initial_count - 3
    
    @pytest.mark.integration
    def test_document_ordering(self, db_session):
        """Test that documents maintain consistent ordering."""
        # Create documents with known titles
        titles = ["Alpha", "Beta", "Gamma"]
        created_ids = []
        
        for title in titles:
            doc_data = DocumentCreate(
                title=title,
                content=f"Content for {title} document."
            )
            response = DocumentService.create_new_document(db_session, doc_data)
            created_ids.append(response.id)
        
        # Retrieve all documents
        documents = DocumentService.get_all_documents(db_session, skip=0, limit=100)
        
        # Filter to our created documents
        our_docs = [doc for doc in documents if doc.id in created_ids]
        
        # Verify all documents are present
        assert len(our_docs) == 3
        
        # Documents should maintain ID order
        doc_ids = [doc.id for doc in our_docs]
        assert doc_ids == sorted(doc_ids)


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling in CRUD and service layers."""
    
    @pytest.mark.integration
    def test_document_not_found_error_message(self, db_session):
        """Test DocumentNotFoundError has helpful message."""
        doc_id = 123456
        
        with pytest.raises(DocumentNotFoundError) as exc_info:
            DocumentService.get_document_by_id(db_session, doc_id)
        
        error_message = str(exc_info.value)
        assert str(doc_id) in error_message
        assert "not found" in error_message.lower()
    
    @pytest.mark.integration
    def test_service_layer_validates_crud_response(self, db_session):
        """Test service layer properly handles None from CRUD layer."""
        # Attempt to get non-existent document
        with pytest.raises(DocumentNotFoundError):
            DocumentService.get_document_by_id(db_session, 999999)
        
        # Attempt to delete non-existent document
        with pytest.raises(DocumentNotFoundError):
            DocumentService.delete_document(db_session, 999999)
    
    @pytest.mark.integration
    def test_update_with_invalid_id(self, db_session):
        """Test updating document with invalid ID returns None."""
        updated = document_crud.update_document(
            db_session,
            -1,  # Invalid ID
            title="Should Not Update"
        )
        
        assert updated is None

