"""
Pydantic schemas for Document validation and serialization.

These schemas are used for request/response validation in FastAPI endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional


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


class DocumentUpdate(BaseModel):
    """
    Schema for updating an existing document (PUT request).
    
    Both fields are optional - only provided fields will be updated.
    At least one field must be provided.
    """
    
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Updated document title (optional)",
        examples=["SOAP Note - Patient Jane Doe (Updated)"]
    )
    content: Optional[str] = Field(
        None,
        min_length=10,
        description="Updated document content (optional)",
        examples=["Subjective: Patient reports improved symptoms..."]
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

class DocumentDeleteResponse(BaseModel):
    """
    Schema for document deletion responses (DELETE requests).
    """
    success: bool = Field(..., description="Success flag")
    message: str = Field(..., description="Success message")
    document_id: int = Field(..., description="Document identifier")
    deleted_at: datetime = Field(..., description="Deletion timestamp")


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


# Document Summary Schemas

class DocumentSummaryBase(BaseModel):
    """
    Base schema for DocumentSummary with shared fields.
    """
    summary_text: str = Field(..., min_length=1, description="LLM-generated summary text")
    model_used: Optional[str] = Field(None, description="LLM model used to generate summary")
    token_usage: Optional[dict] = Field(None, description="Token usage statistics")


class DocumentSummaryCreate(DocumentSummaryBase):
    """
    Schema for creating a new document summary (internal use).
    """
    document_id: int = Field(..., description="Document ID this summary belongs to")


class DocumentSummaryResponse(DocumentSummaryBase):
    """
    Schema for document summary responses.
    
    Includes all fields plus id, document_id, and timestamps.
    """
    id: int = Field(..., description="Unique summary identifier")
    document_id: int = Field(..., description="Document ID this summary belongs to")
    created_at: datetime = Field(..., description="Summary creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)

