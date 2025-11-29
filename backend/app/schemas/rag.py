"""
Pydantic schemas for RAG operations validation and serialization.

These schemas are used for request/response validation in RAG-related endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class QuestionRequest(BaseModel):
    """
    Used by POST /rag/answer_question endpoint.
    """
    
    question: str = Field(
        ...,
        min_length=5,
        description="Question to answer using the document knowledge base",
        examples=[
            "What medications are mentioned in the notes?",
            "What are the patient's vital signs?",
            "What follow-up appointments were scheduled?"
        ]
    )
    
    top_k: Optional[int] = Field(
        None,
        ge=1,
        le=10,
        description="Number of document chunks to retrieve (default: from config)",
        examples=[3, 5]
    )
    
    similarity_threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score (0-1) for retrieved chunks",
        examples=[0.7, 0.8]
    )
    
    model: Optional[str] = Field(
        None,
        description="Optional: Override the default LLM model",
        examples=["gpt-5-nano", "gpt-5-mini"]
    )


class SourceChunk(BaseModel):
    """
    Represents a document chunk that was used as context for answering.
    """
    document_id: int = Field(..., description="ID of the source document")
    document_title: str = Field(..., description="Title of the source document")
    chunk_index: int = Field(..., description="Index of this chunk within the document")
    chunk_text: str = Field(..., description="Text content of the chunk")
    similarity_score: float = Field(..., description="Similarity score (0-1) between query and chunk")


class TokenUsage(BaseModel):
    """Schema for token usage information."""
    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_tokens: int = Field(..., description="Total tokens used")


class AnswerResponse(BaseModel):
    """
    Returns the answer along with source citations and metadata.
    """
    answer: str = Field(..., description="The generated answer to the question")
    sources: List[SourceChunk] = Field(..., description="List of source chunks used to generate the answer")
    model_used: str = Field(..., description="The LLM model used for answer generation")
    token_usage: TokenUsage = Field(..., description="Token usage statistics")
    processing_time_ms: int = Field(..., description="Total processing time in milliseconds")
    retrieval_time_ms: int = Field(..., description="Time spent on retrieval in milliseconds")
    generation_time_ms: int = Field(..., description="Time spent on LLM generation in milliseconds")


class EmbedDocumentResponse(BaseModel):
    """
    Returns metadata about the embedding operation.
    """
    document_id: int = Field(..., description="ID of the embedded document")
    document_title: str = Field(..., description="Title of the embedded document")
    chunks_created: int = Field(..., description="Number of chunks created")
    embeddings_created: int = Field(..., description="Number of embeddings created")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    skipped: bool = Field(..., description="Whether the document was skipped (already embedded)")
    existing_embeddings: Optional[int] = Field(None, description="Number of existing embeddings (if skipped)")


class DocumentEmbeddingResult(BaseModel):
    """Schema for individual document embedding result in batch operations."""
    document_id: int
    document_title: str
    chunks_created: int
    embeddings_created: int
    skipped: bool
    error: Optional[str] = None


class EmbedAllResponse(BaseModel):
    """
    Returns aggregate statistics for embedding multiple documents.
    """
    documents_processed: int = Field(..., description="Number of documents successfully processed")
    documents_skipped: int = Field(..., description="Number of documents skipped (already embedded)")
    total_chunks: int = Field(..., description="Total number of chunks created")
    total_embeddings: int = Field(...,description="Total number of embeddings created")
    processing_time_ms: int = Field(..., description="Total processing time in milliseconds")
    results: List[DocumentEmbeddingResult] = Field(..., description="Per-document results")


class RAGStatsResponse(BaseModel):
    """
    Provides overview of the RAG system state.
    """
    total_documents: int = Field(..., description="Total number of documents in the database")
    total_embeddings: int = Field(..., description="Total number of embeddings stored")
    documents_with_embeddings: int = Field(..., description="Number of documents that have embeddings")
    avg_chunks_per_document: float = Field(..., description="Average number of chunks per document")
    embedding_dimension: int = Field(..., description="Dimension of embedding vectors")
    embedding_model: str = Field(..., description="Embedding model being used")
    chunk_size: int = Field(..., description="Target chunk size in characters")
    chunk_overlap: int = Field(..., description="Overlap between chunks in characters")
    rag_top_k: int = Field(..., description="Default number of chunks to retrieve for RAG")

class ErrorResponse(BaseModel):
    """
    Provides consistent error formatting.
    """
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Detailed error message")
    status_code: int = Field(..., description="HTTP status code")

