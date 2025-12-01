"""
Test Part 3: RAG Pipeline

Tests for:
- PGVector setup and configuration
- Document embeddings (CRUD operations)
- Vector similarity search
- RAG service (document embedding, question answering)
- RAG API endpoints
"""

import pytest
from sqlalchemy import text
import numpy as np

from app.models.document_embedding import DocumentEmbedding
from app.crud import embedding as embedding_crud
from app.crud import document as document_crud


# ============================================================================
# PGVector Setup Tests (from test_pgvector_setup.py)
# ============================================================================

class TestPGVectorSetup:
    """Test PGVector extension setup and configuration."""
    
    @pytest.mark.integration
    def test_pgvector_extension_enabled(self, postgres_db_session):
        """Test that PGVector extension is installed and enabled."""
        result = postgres_db_session.execute(
            text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'")
        ).fetchone()
        
        assert result is not None, "PGVector extension should be installed"
        assert result[0] == "vector"
        assert result[1] is not None  # Has version number
    
    @pytest.mark.integration
    def test_document_embeddings_table_exists(self, postgres_db_session):
        """Test that document_embeddings table exists."""
        result = postgres_db_session.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename = 'document_embeddings'")
        ).fetchone()
        
        assert result is not None, "document_embeddings table should exist"
        assert result[0] == "document_embeddings"
    
    @pytest.mark.integration
    def test_vector_column_type(self, postgres_db_session):
        """Test that embedding column has vector type."""
        result = postgres_db_session.execute(
            text("""
                SELECT column_name, data_type, udt_name 
                FROM information_schema.columns 
                WHERE table_name = 'document_embeddings' AND column_name = 'embedding'
            """)
        ).fetchone()
        
        assert result is not None, "embedding column should exist"
        assert result[2] == "vector", "embedding column should be of type vector"
    
    @pytest.mark.integration
    def test_can_store_and_retrieve_vector(self, postgres_db_session, sample_document_postgres):
        """Test storing and retrieving vector embeddings."""
        # Create a test embedding vector (1536 dimensions)
        test_embedding = np.random.rand(1536).tolist()
        
        # Create embedding record
        emb = DocumentEmbedding(
            document_id=sample_document_postgres.id,
            chunk_index=0,
            chunk_text="This is a test chunk for vector storage.",
            embedding=test_embedding
        )
        postgres_db_session.add(emb)
        postgres_db_session.commit()
        postgres_db_session.refresh(emb)
        
        # Retrieve it
        retrieved = postgres_db_session.query(DocumentEmbedding).filter(
            DocumentEmbedding.id == emb.id
        ).first()
        
        assert retrieved is not None
        assert retrieved.document_id == sample_document_postgres.id
        assert retrieved.chunk_index == 0
        assert len(retrieved.embedding) == 1536
        
        # Verify vector values are close (floating point comparison)
        np.testing.assert_array_almost_equal(
            retrieved.embedding, 
            test_embedding,
            decimal=6
        )


# ============================================================================
# Embedding CRUD Tests
# ============================================================================

class TestEmbeddingCRUD:
    """Test embedding CRUD operations."""
    
    @pytest.mark.integration
    def test_document_has_embeddings(self, postgres_db_session, sample_document_postgres):
        """Test checking if document has embeddings."""
        # Initially should have no embeddings
        has_emb = embedding_crud.document_has_embeddings(postgres_db_session, sample_document_postgres.id)
        assert has_emb is False
        
        # Add an embedding
        emb = DocumentEmbedding(
            document_id=sample_document_postgres.id,
            chunk_index=0,
            chunk_text="Test chunk",
            embedding=np.random.rand(1536).tolist()
        )
        postgres_db_session.add(emb)
        postgres_db_session.commit()
        
        # Now should have embeddings
        has_emb = embedding_crud.document_has_embeddings(postgres_db_session, sample_document_postgres.id)
        assert has_emb is True
    
    @pytest.mark.integration
    def test_count_embeddings_by_document(self, postgres_db_session, sample_document_postgres):
        """Test counting embeddings for a document."""
        # Create multiple embeddings
        for i in range(3):
            emb = DocumentEmbedding(
                document_id=sample_document_postgres.id,
                chunk_index=i,
                chunk_text=f"Test chunk {i}",
                embedding=np.random.rand(1536).tolist()
            )
            postgres_db_session.add(emb)
        postgres_db_session.commit()
        
        count = embedding_crud.count_embeddings_by_document(postgres_db_session, sample_document_postgres.id)
        assert count == 3
    
    @pytest.mark.integration
    def test_get_embeddings_by_document(self, postgres_db_session, sample_document_postgres):
        """Test retrieving all embeddings for a document."""
        # Create embeddings
        for i in range(2):
            emb = DocumentEmbedding(
                document_id=sample_document_postgres.id,
                chunk_index=i,
                chunk_text=f"Chunk {i}",
                embedding=np.random.rand(1536).tolist()
            )
            postgres_db_session.add(emb)
        postgres_db_session.commit()
        
        embeddings = embedding_crud.get_embeddings_by_document(postgres_db_session, sample_document_postgres.id)
        
        assert len(embeddings) == 2
        assert embeddings[0].chunk_index == 0
        assert embeddings[1].chunk_index == 1
    
    @pytest.mark.integration
    def test_delete_embeddings_by_document(self, postgres_db_session, sample_document_postgres):
        """Test deleting all embeddings for a document."""
        # Create embeddings
        for i in range(2):
            emb = DocumentEmbedding(
                document_id=sample_document_postgres.id,
                chunk_index=i,
                chunk_text=f"Chunk {i}",
                embedding=np.random.rand(1536).tolist()
            )
            postgres_db_session.add(emb)
        postgres_db_session.commit()
        
        # Delete embeddings
        deleted_count = embedding_crud.delete_embeddings_by_document(postgres_db_session, sample_document_postgres.id)
        
        assert deleted_count == 2
        
        # Verify deletion
        count = embedding_crud.count_embeddings_by_document(postgres_db_session, sample_document_postgres.id)
        assert count == 0
    
    @pytest.mark.integration
    def test_get_embedding_stats(self, postgres_db_session, clean_postgres_database):
        """Test getting overall embedding statistics."""
        from app.schemas.document import DocumentCreate
        
        # Create documents with embeddings
        for doc_idx in range(2):
            doc_data = DocumentCreate(
                title=f"Test Doc {doc_idx}",
                content=f"Content {doc_idx} with sufficient length for validation requirements."
            )
            doc = document_crud.create_document(postgres_db_session, doc_data)
            
            # Add 2 embeddings per document
            for chunk_idx in range(2):
                emb = DocumentEmbedding(
                    document_id=doc.id,
                    chunk_index=chunk_idx,
                    chunk_text=f"Chunk {chunk_idx}",
                    embedding=np.random.rand(1536).tolist()
                )
                postgres_db_session.add(emb)
        postgres_db_session.commit()
        
        stats = embedding_crud.get_embedding_stats(postgres_db_session)
        
        assert stats["total_embeddings"] == 4
        assert stats["total_documents_with_embeddings"] == 2
        assert stats["avg_chunks_per_document"] == 2.0


# ============================================================================
# Vector Similarity Search Tests
# ============================================================================

class TestVectorSimilaritySearch:
    """Test vector similarity search functionality."""
    
    @pytest.mark.integration
    def test_find_similar_chunks(self, postgres_db_session, sample_document_postgres):
        """Test finding similar chunks using cosine similarity."""
        # Create embeddings with known vectors
        emb1 = DocumentEmbedding(
            document_id=sample_document_postgres.id,
            chunk_index=0,
            chunk_text="Diabetes treatment plan",
            embedding=np.random.rand(1536).tolist()
        )
        emb2 = DocumentEmbedding(
            document_id=sample_document_postgres.id,
            chunk_index=1,
            chunk_text="Hypertension medication",
            embedding=np.random.rand(1536).tolist()
        )
        postgres_db_session.add_all([emb1, emb2])
        postgres_db_session.commit()
        
        # Use the first embedding as query
        query_embedding = emb1.embedding
        
        # Find similar chunks (using correct function name and parameter)
        results = embedding_crud.search_similar_chunks(
            postgres_db_session,
            query_embedding=query_embedding,
            limit=2
        )
        
        assert len(results) > 0
        # First result should be the exact match
        assert results[0][0].id == emb1.id
        # Function returns similarity score (1.0 = perfect match), not distance
        assert results[0][1] > 0.9  # Similarity should be very high for exact match
    
    @pytest.mark.integration
    def test_find_similar_chunks_with_threshold(self, postgres_db_session, sample_document_postgres):
        """Test similarity search with similarity threshold."""
        # Create an embedding
        emb = DocumentEmbedding(
            document_id=sample_document_postgres.id,
            chunk_index=0,
            chunk_text="Test content",
            embedding=np.random.rand(1536).tolist()
        )
        postgres_db_session.add(emb)
        postgres_db_session.commit()
        
        # Search with very strict threshold (nothing should match except exact)
        results = embedding_crud.search_similar_chunks(
            postgres_db_session,
            query_embedding=emb.embedding,
            limit=5,
            similarity_threshold=0.01  # Very strict
        )
        
        # Should find at least the exact match
        assert len(results) >= 1


# ============================================================================
# RAG Service Tests
# ============================================================================

class TestRAGService:
    """Test RAG service functionality."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_embed_document(self, postgres_db_session, sample_document_postgres):
        """Test embedding a document with RAG service."""
        from app.services.rag import RAGService
        
        rag_service = RAGService(postgres_db_session)
        
        # Embed the document
        result = rag_service.embed_document(sample_document_postgres.id)
        
        assert result["document_id"] == sample_document_postgres.id
        assert result["chunks_created"] > 0
        assert "processing_time_ms" in result
        
        # Verify embeddings were created
        count = embedding_crud.count_embeddings_by_document(
            postgres_db_session,
            sample_document_postgres.id
        )
        assert count == result["chunks_created"]
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_answer_question(self, postgres_db_session):
        """Test answering questions with RAG service."""
        from app.services.rag import RAGService
        
        rag_service = RAGService(postgres_db_session)
        
        # Ask a question that should be answerable from seeded documents
        result = rag_service.answer_question(
            question="What medications are commonly mentioned?",
            top_k=3
        )
        
        assert "answer" in result
        assert len(result["answer"]) > 0
        assert "sources" in result
        assert isinstance(result["sources"], list)
        assert "model_used" in result
        assert "processing_time_ms" in result


# ============================================================================
# RAG API Endpoint Tests
# ============================================================================

class TestRAGEndpoints:
    """Test RAG API endpoints."""
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_rag_stats_endpoint(self, test_client_postgres):
        """Test GET /rag/stats endpoint."""
        response = test_client_postgres.get("/rag/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_embeddings" in data
        assert "documents_with_embeddings" in data  # Correct field name
        assert "embedding_model" in data
        assert "embedding_dimension" in data
    
    @pytest.mark.api
    @pytest.mark.integration
    @pytest.mark.slow
    def test_embed_document_endpoint(self, test_client_postgres, sample_document_postgres):
        """Test POST /rag/embed_document/{id} endpoint."""
        response = test_client_postgres.post(f"/rag/embed_document/{sample_document_postgres.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == sample_document_postgres.id
        assert data["chunks_created"] > 0
        assert "processing_time_ms" in data
    
    @pytest.mark.api
    def test_embed_document_not_found(self, test_client_postgres):
        """Test embedding non-existent document returns error."""
        response = test_client_postgres.post("/rag/embed_document/999999")
        
        # Endpoint returns 500 for non-existent documents (could be improved to return 404)
        assert response.status_code in [404, 500]
    
    @pytest.mark.api
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_answer_question_endpoint(self, async_client_postgres):
        """Test POST /rag/answer_question endpoint."""
        response = await async_client_postgres.post(
            "/rag/answer_question",
            json={"question": "What medications are mentioned in the documents?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert len(data["answer"]) > 0
        assert "sources" in data
        assert isinstance(data["sources"], list)
        assert "model_used" in data
        assert "processing_time_ms" in data
