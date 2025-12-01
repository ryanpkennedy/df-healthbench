"""
Test Part 1: Backend Foundation

Tests for:
- Database setup and connection
- Table creation
- Health check endpoints
- Document CRUD API endpoints
- Pydantic schema validation
"""

import pytest
from sqlalchemy import text

from app.models.document import Document
from app.schemas.document import DocumentCreate
from pydantic import ValidationError


# ============================================================================
# Database Setup Tests
# ============================================================================

class TestDatabaseSetup:
    """Test database configuration and connectivity."""
    
    @pytest.mark.integration
    def test_database_connection_sqlite(self, db_session):
        """Test SQLite database connection works."""
        result = db_session.execute(text("SELECT 1")).scalar()
        assert result == 1
    
    @pytest.mark.integration
    def test_database_connection_postgres(self, postgres_db_session):
        """Test PostgreSQL database connection works."""
        result = postgres_db_session.execute(text("SELECT 1")).scalar()
        assert result == 1
    
    @pytest.mark.integration
    def test_tables_exist_sqlite(self, db_session):
        """Test that all required tables exist in SQLite."""
        # Query sqlite_master to check tables
        result = db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        ).fetchall()
        assert len(result) > 0, "documents table should exist"
    
    @pytest.mark.integration
    def test_tables_exist_postgres(self, postgres_db_session):
        """Test that all required tables exist in PostgreSQL."""
        # Query information_schema to check tables
        result = postgres_db_session.execute(
            text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('documents', 'document_embeddings', 'document_summary')
            """)
        ).fetchall()
        assert len(result) == 3, "All three tables (documents, document_embeddings, document_summary) should exist"
    
    @pytest.mark.integration
    def test_pgvector_extension_installed(self, postgres_db_session):
        """Test that pgvector extension is installed in PostgreSQL."""
        result = postgres_db_session.execute(
            text("SELECT * FROM pg_extension WHERE extname = 'vector'")
        ).fetchone()
        assert result is not None, "pgvector extension should be installed"


# ============================================================================
# Schema Validation Tests
# ============================================================================

class TestSchemaValidation:
    """Test Pydantic schema validation."""
    
    @pytest.mark.unit
    def test_document_create_valid(self):
        """Test DocumentCreate schema with valid data."""
        doc = DocumentCreate(
            title="Test Document",
            content="This is test content with at least 10 characters."
        )
        assert doc.title == "Test Document"
        assert len(doc.content) >= 10
    
    @pytest.mark.unit
    def test_document_create_content_too_short(self):
        """Test DocumentCreate validation rejects short content."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(title="Test", content="Short")
        
        # Check that the error is about content length
        errors = exc_info.value.errors()
        assert any("content" in str(error.get("loc")) for error in errors)
    
    @pytest.mark.unit
    def test_document_create_missing_title(self):
        """Test DocumentCreate validation requires title."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(content="This is valid content that is long enough.")
        
        errors = exc_info.value.errors()
        assert any("title" in str(error.get("loc")) for error in errors)
    
    @pytest.mark.unit
    def test_document_create_missing_content(self):
        """Test DocumentCreate validation requires content."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(title="Test Document")
        
        errors = exc_info.value.errors()
        assert any("content" in str(error.get("loc")) for error in errors)


# ============================================================================
# Model Tests
# ============================================================================

class TestDocumentModel:
    """Test Document SQLAlchemy model."""
    
    @pytest.mark.integration
    def test_create_document(self, db_session):
        """Test creating a document with the ORM."""
        doc = Document(
            title="Test SOAP Note",
            content="Subjective: Test patient reports test symptoms."
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)
        
        assert doc.id is not None
        assert doc.title == "Test SOAP Note"
        assert doc.created_at is not None
        assert doc.updated_at is not None
    
    @pytest.mark.integration
    def test_document_timestamps(self, db_session):
        """Test that created_at and updated_at are set automatically."""
        doc = Document(
            title="Timestamp Test",
            content="Testing automatic timestamp creation."
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)
        
        assert doc.created_at is not None
        assert doc.updated_at is not None
        # For new documents, created_at should equal updated_at
        assert doc.created_at == doc.updated_at


# ============================================================================
# Health Check Endpoint Tests
# ============================================================================

class TestHealthEndpoints:
    """Test health check API endpoints."""
    
    @pytest.mark.api
    def test_health_check(self, test_client):
        """Test GET /health returns ok status."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_health_db_check_sqlite(self, test_client):
        """Test GET /health/db with SQLite database."""
        response = test_client.get("/health/db")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "database" in data
        assert data["database"] == "connected"
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_health_db_check_postgres(self, test_client_postgres):
        """Test GET /health/db with PostgreSQL database."""
        response = test_client_postgres.get("/health/db")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"


# ============================================================================
# Root Endpoint Tests
# ============================================================================

class TestRootEndpoint:
    """Test root API endpoint."""
    
    @pytest.mark.api
    def test_root_endpoint(self, test_client):
        """Test GET / returns API information."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "DF HealthBench API"


# ============================================================================
# Document CRUD Endpoint Tests
# ============================================================================

class TestDocumentEndpoints:
    """Test document CRUD API endpoints."""
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_list_documents_empty(self, test_client, clean_database):
        """Test GET /documents with empty database."""
        response = test_client.get("/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert "document_ids" in data
        assert "count" in data
        assert data["count"] == 0
        assert data["document_ids"] == []
    
    @pytest.mark.api
    @pytest.mark.integration
    @pytest.mark.skip(reason="SQLite TestClient has issues with async POST - tested with postgres")
    def test_create_document(self, test_client):
        """Test POST /documents creates a new document."""
        doc_data = {
            "title": "API Test Document",
            "content": "This is a test document created via the API to verify POST endpoint functionality."
        }
        response = test_client.post("/documents", json=doc_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == doc_data["title"]
        assert data["content"] == doc_data["content"]
        assert "created_at" in data
        assert "updated_at" in data
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_create_document_postgres(self, test_client_postgres):
        """Test POST /documents creates a new document (PostgreSQL)."""
        doc_data = {
            "title": "API Test Document",
            "content": "This is a test document created via the API to verify POST endpoint functionality."
        }
        response = test_client_postgres.post("/documents", json=doc_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == doc_data["title"]
        assert data["content"] == doc_data["content"]
        assert "created_at" in data
        assert "updated_at" in data
    
    @pytest.mark.api
    @pytest.mark.integration
    @pytest.mark.skip(reason="SQLite TestClient has issues with async POST - tested with postgres")
    def test_create_document_invalid_content(self, test_client):
        """Test POST /documents rejects invalid content."""
        doc_data = {
            "title": "Invalid Document",
            "content": "Short"  # Too short
        }
        response = test_client.post("/documents", json=doc_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_get_document_by_id(self, test_client, sample_document):
        """Test GET /documents/{id} retrieves specific document."""
        response = test_client.get(f"/documents/{sample_document.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_document.id
        assert data["title"] == sample_document.title
        assert data["content"] == sample_document.content
    
    @pytest.mark.api
    def test_get_document_not_found(self, test_client):
        """Test GET /documents/{id} returns 404 for non-existent document."""
        response = test_client.get("/documents/999999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_list_all_documents_detailed(self, test_client, sample_document):
        """Test GET /documents/list/all returns detailed document list."""
        response = test_client.get("/documents/list/all")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check first document has all required fields
        doc = data[0]
        assert "id" in doc
        assert "title" in doc
        assert "content" in doc
        assert "created_at" in doc
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_list_documents_pagination(self, test_client, sample_document):
        """Test GET /documents/list/all supports pagination."""
        # Test with limit
        response = test_client.get("/documents/list/all?limit=1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 1
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_delete_document(self, test_client, sample_document):
        """Test DELETE /documents/{id} deletes document."""
        doc_id = sample_document.id
        
        response = test_client.delete(f"/documents/{doc_id}")
        
        # DELETE returns 200 with JSON body, not 204 No Content
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify document is deleted
        get_response = test_client.get(f"/documents/{doc_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_delete_document_postgres(self, test_client_postgres, sample_document_postgres):
        """Test DELETE /documents/{id} deletes document (PostgreSQL)."""
        doc_id = sample_document_postgres.id
        
        response = test_client_postgres.delete(f"/documents/{doc_id}")
        
        # DELETE returns 200 with JSON body
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify document is deleted
        get_response = test_client_postgres.get(f"/documents/{doc_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.api
    def test_delete_document_not_found(self, test_client):
        """Test DELETE /documents/{id} returns 404 for non-existent document."""
        response = test_client.delete("/documents/999999")
        
        assert response.status_code == 404


# ============================================================================
# API Documentation Tests
# ============================================================================

class TestAPIDocumentation:
    """Test API documentation endpoints."""
    
    @pytest.mark.api
    def test_swagger_ui_accessible(self, test_client):
        """Test GET /docs returns Swagger UI."""
        response = test_client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.api
    def test_openapi_json_accessible(self, test_client):
        """Test GET /openapi.json returns OpenAPI schema."""
        response = test_client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

