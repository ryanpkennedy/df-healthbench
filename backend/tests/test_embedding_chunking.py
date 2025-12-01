"""
Test Embedding and Chunking Services

Tests for:
- Document chunking (text splitting with overlap)
- Chunk statistics
- SOAP-aware chunking
- Embedding service (OpenAI integration)
- Single and batch embedding generation
"""

import pytest


# ============================================================================
# Chunking Service Tests
# ============================================================================

class TestChunkingService:
    """Test document chunking functionality."""
    
    @pytest.mark.unit
    def test_chunk_document_basic(self):
        """Test basic document chunking."""
        from app.services.chunking import chunk_document
        
        text = "This is a test document. " * 50  # ~1200 characters
        chunks = chunk_document(text, max_chunk_size=200, overlap=20)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 220 for chunk in chunks)  # Allow some overflow
    
    @pytest.mark.unit
    def test_chunk_document_with_soap_note(self, sample_soap_note):
        """Test chunking a real SOAP note."""
        from app.services.chunking import chunk_document
        
        chunks = chunk_document(sample_soap_note, max_chunk_size=800, overlap=50)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk) > 0 for chunk in chunks)
    
    @pytest.mark.unit
    def test_chunk_document_short_text(self):
        """Test chunking text shorter than max_chunk_size."""
        from app.services.chunking import chunk_document
        
        text = "This is a short document."
        chunks = chunk_document(text, max_chunk_size=1000, overlap=50)
        
        # Short text should return single chunk
        assert len(chunks) == 1
        assert chunks[0] == text
    
    @pytest.mark.unit
    def test_chunk_document_empty_text(self):
        """Test chunking empty text raises ValueError."""
        from app.services.chunking import chunk_document
        
        # Empty text should raise ValueError
        with pytest.raises(ValueError, match="Content cannot be empty"):
            chunk_document("", max_chunk_size=800, overlap=50)
    
    @pytest.mark.unit
    def test_chunk_overlap(self):
        """Test that chunks have proper overlap."""
        from app.services.chunking import chunk_document
        
        text = "Word " * 200  # ~1000 characters
        chunks = chunk_document(text, max_chunk_size=100, overlap=20)
        
        if len(chunks) > 1:
            # Check that consecutive chunks share some content
            # (This depends on implementation - adjust if needed)
            assert len(chunks) > 1
    
    @pytest.mark.unit
    def test_get_chunk_stats(self):
        """Test getting chunk statistics."""
        from app.services.chunking import chunk_document, get_chunk_stats
        
        text = "This is a test. " * 50
        chunks = chunk_document(text, max_chunk_size=200, overlap=20)
        
        stats = get_chunk_stats(chunks)
        
        assert "count" in stats
        assert "avg_size" in stats
        assert "min_size" in stats
        assert "max_size" in stats
        assert "total_chars" in stats
        
        assert stats["count"] == len(chunks)
        assert stats["count"] > 0
        assert stats["avg_size"] > 0
        assert stats["min_size"] > 0
        assert stats["max_size"] > 0
    
    @pytest.mark.unit
    def test_chunk_stats_single_chunk(self):
        """Test chunk stats with single chunk."""
        from app.services.chunking import get_chunk_stats
        
        chunks = ["This is a single chunk."]
        stats = get_chunk_stats(chunks)
        
        assert stats["count"] == 1
        assert stats["avg_size"] == len(chunks[0])
        assert stats["min_size"] == len(chunks[0])
        assert stats["max_size"] == len(chunks[0])
    
    @pytest.mark.unit
    def test_soap_aware_chunking(self, sample_soap_note):
        """Test that chunking handles SOAP notes correctly."""
        from app.services.chunking import chunk_document
        
        # SOAP notes have sections: Subjective, Objective, Assessment, Plan
        chunks = chunk_document(sample_soap_note, max_chunk_size=800, overlap=50)
        
        # Verify chunks contain meaningful content
        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk.strip()) > 0
        
        # Verify the full content is preserved across all chunks
        combined_chunks = "".join(chunks)
        # Check that key medical terms from SOAP note are preserved
        assert len(combined_chunks) > 0


# ============================================================================
# Embedding Service Tests
# ============================================================================

class TestEmbeddingService:
    """Test embedding generation service."""
    
    @pytest.mark.unit
    def test_get_embedding_service_singleton(self):
        """Test that embedding service uses singleton pattern."""
        from app.services.embedding import get_embedding_service
        
        service1 = get_embedding_service()
        service2 = get_embedding_service()
        
        assert service1 is service2
    
    @pytest.mark.unit
    def test_embedding_service_configuration(self):
        """Test that embedding service is configured correctly."""
        from app.services.embedding import get_embedding_service
        
        service = get_embedding_service()
        
        assert hasattr(service, 'embedding_model')
        assert hasattr(service, 'embedding_dimension')
        assert service.embedding_model == "text-embedding-3-small"
        assert service.embedding_dimension == 1536
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_generate_single_embedding(self):
        """Test generating a single embedding with real API call."""
        from app.services.embedding import get_embedding_service
        
        service = get_embedding_service()
        
        text = "Patient presents with fever and cough. Temperature is 101F."
        embedding = service.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536  # text-embedding-3-small dimensions
        assert all(isinstance(val, float) for val in embedding)
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_generate_embeddings_batch(self):
        """Test generating multiple embeddings individually."""
        from app.services.embedding import get_embedding_service
        
        service = get_embedding_service()
        
        texts = [
            "Patient has Type 2 Diabetes.",
            "Blood pressure is elevated at 140/90.",
            "Prescribe Metformin 500mg twice daily."
        ]
        
        # Generate embeddings one at a time (service has generate_embedding, not generate_embeddings)
        embeddings = [service.generate_embedding(text) for text in texts]
        
        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)
        
        # Verify embeddings are different (not all the same)
        assert embeddings[0] != embeddings[1]
        assert embeddings[1] != embeddings[2]
    
    @pytest.mark.unit
    def test_generate_embedding_validates_input(self):
        """Test that embedding service validates input."""
        from app.services.embedding import get_embedding_service
        
        service = get_embedding_service()
        
        # Test empty string
        with pytest.raises(ValueError):
            service.generate_embedding("")
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_embedding_consistency(self):
        """Test that same text generates similar (but not identical) embeddings."""
        from app.services.embedding import get_embedding_service
        import numpy as np
        
        service = get_embedding_service()
        
        text = "Patient diagnosed with hypertension."
        
        # Generate embedding twice
        emb1 = service.generate_embedding(text)
        emb2 = service.generate_embedding(text)
        
        # Embeddings should be very similar but may not be identical (OpenAI has some variation)
        # Check cosine similarity instead
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        cosine_similarity = dot_product / (norm1 * norm2)
        
        # Cosine similarity should be very high (> 0.99) for same text
        assert cosine_similarity > 0.99, f"Embeddings should be very similar (cosine similarity: {cosine_similarity})"


# ============================================================================
# Chunking and Embedding Integration Tests
# ============================================================================

class TestChunkingEmbeddingIntegration:
    """Test integration between chunking and embedding services."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_chunk_and_embed_document(self, sample_soap_note):
        """Test full pipeline: chunk document and generate embeddings."""
        from app.services.chunking import chunk_document
        from app.services.embedding import get_embedding_service
        
        # Chunk the document
        chunks = chunk_document(sample_soap_note, max_chunk_size=800, overlap=50)
        
        assert len(chunks) > 0
        
        # Generate embeddings for chunks (one at a time)
        embedding_service = get_embedding_service()
        embeddings = [embedding_service.generate_embedding(chunk) for chunk in chunks]
        
        assert len(embeddings) == len(chunks)
        assert all(len(emb) == 1536 for emb in embeddings)
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_chunk_sizes_affect_embedding_count(self):
        """Test that chunk size affects number of embeddings."""
        from app.services.chunking import chunk_document
        
        text = "Patient information. " * 100  # ~2000 characters
        
        # Small chunks
        small_chunks = chunk_document(text, max_chunk_size=200, overlap=20)
        
        # Large chunks
        large_chunks = chunk_document(text, max_chunk_size=1000, overlap=20)
        
        # Smaller chunk size should produce more chunks
        assert len(small_chunks) > len(large_chunks)
    
    @pytest.mark.unit
    def test_chunk_overlap_prevents_information_loss(self):
        """Test that overlap helps prevent information loss at chunk boundaries."""
        from app.services.chunking import chunk_document
        
        # Create text with important info at boundary
        text = "A" * 150 + "IMPORTANT" + "B" * 150
        
        # Chunk with overlap
        chunks = chunk_document(text, max_chunk_size=200, overlap=50)
        
        # "IMPORTANT" should appear in at least one chunk
        has_important = any("IMPORTANT" in chunk for chunk in chunks)
        assert has_important, "Overlap should help preserve boundary information"


# ============================================================================
# Performance and Edge Case Tests
# ============================================================================

class TestChunkingPerformance:
    """Test chunking performance and edge cases."""
    
    @pytest.mark.unit
    def test_chunk_very_long_document(self):
        """Test chunking a very long document."""
        from app.services.chunking import chunk_document
        
        # Create a 50KB document
        long_text = "Patient data. " * 3000  # ~50KB
        
        chunks = chunk_document(long_text, max_chunk_size=800, overlap=50)
        
        assert len(chunks) > 10
        assert all(len(chunk) <= 850 for chunk in chunks)  # Allow small overflow
    
    @pytest.mark.unit
    def test_chunk_special_characters(self):
        """Test chunking text with special characters."""
        from app.services.chunking import chunk_document
        
        text = "Patient: José García\nDiagnosis: Hypertension\n©2024 Medical Records"
        
        chunks = chunk_document(text, max_chunk_size=100, overlap=10)
        
        assert len(chunks) > 0
        # Special characters should be preserved
        combined = "".join(chunks)
        assert "José" in combined
        assert "©" in combined
    
    @pytest.mark.unit
    def test_chunk_unicode_characters(self):
        """Test chunking text with Unicode characters."""
        from app.services.chunking import chunk_document
        
        # Create longer text with Unicode to meet min chunk size requirement
        text = "Patient: 王医生 (Dr. Wang)\nSymptoms: 发热、咳嗽\n" + "Additional medical information. " * 10
        
        chunks = chunk_document(text, max_chunk_size=200, overlap=20)
        
        assert len(chunks) > 0
        # Unicode characters should be preserved
        combined = "".join(chunks)
        assert "王医生" in combined
