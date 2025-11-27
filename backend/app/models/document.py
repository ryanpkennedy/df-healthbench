"""
SQLAlchemy model for Document entity.

This module defines the Document table structure for storing
medical documents (SOAP notes, etc.) in the database.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Document(Base):
    """
    Document model for storing medical documents.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        title: Document title (max 255 characters)
        content: Full document text content
        created_at: Timestamp when document was created
        updated_at: Timestamp when document was last updated
    """
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        """String representation of Document for debugging."""
        return f"<Document(id={self.id}, title='{self.title[:30]}...', created_at={self.created_at})>"

