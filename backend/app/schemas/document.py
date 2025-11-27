"""
Pydantic schemas for Document validation and serialization.

These schemas are used for request/response validation in FastAPI endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List


class DocumentBase(BaseModel):
    """
    Base schema with shared fields for Document.
    
    This is inherited by other schemas to avoid duplication.
    """
    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    content: str = Field(..., min_length=1, description="Document content")


class DocumentCreate(DocumentBase):
    """
    Schema for creating a new document (POST request).
    
    Inherits title and content from DocumentBase.
    Adds additional validation rules for creation.
    """
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Document title",
        examples=["SOAP Note - Patient John Doe"]
    )
    content: str = Field(
        ...,
        min_length=10,  # Require at least 10 characters for content
        description="Document content",
        examples=["Subjective: Patient reports fever..."]
    )


class DocumentResponse(DocumentBase):
    """
    Schema for document responses (GET requests).
    
    Includes all fields from DocumentBase plus id and timestamps.
    Configured to work with SQLAlchemy ORM models.
    """
    
    id: int = Field(..., description="Unique document identifier")
    created_at: datetime = Field(..., description="Document creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """
    Schema for listing document IDs.
    
    Used by GET /documents endpoint to return list of all document IDs.
    """
    
    document_ids: List[int] = Field(
        default_factory=list,
        description="List of document IDs"
    )
    count: int = Field(..., description="Total number of documents")

