"""
SQLAlchemy model for DocumentEmbedding entity.

This module defines the DocumentEmbedding table structure for storing
vector embeddings of document chunks for semantic search using PGVector.
"""

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database import Base


class DocumentEmbedding(Base):
    """
    DocumentEmbedding model for storing vector embeddings of document chunks.
    
    This table stores chunked document text along with their vector embeddings
    for semantic similarity search using PGVector extension.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        document_id: Foreign key to documents table
        chunk_index: Index of this chunk within the document (0-based)
        chunk_text: The actual text content of this chunk
        embedding: Vector embedding (1536 dimensions for text-embedding-3-small)
        created_at: Timestamp when embedding was created
        
    Relationships:
        document: Reference to the parent Document
    """
    
    __tablename__ = "document_embeddings"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=False)  # text-embedding-3-small produces 1536-dim vectors
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship to Document
    document = relationship("Document", backref="embeddings")
    
    # Composite index for efficient chunk retrieval by document
    __table_args__ = (
        Index('idx_document_chunk', 'document_id', 'chunk_index'),
    )
    
    def __repr__(self) -> str:
        """String representation of DocumentEmbedding for debugging."""
        chunk_preview = self.chunk_text[:50] if self.chunk_text else ""
        return (
            f"<DocumentEmbedding(id={self.id}, document_id={self.document_id}, "
            f"chunk_index={self.chunk_index}, chunk_preview='{chunk_preview}...')>"
        )

