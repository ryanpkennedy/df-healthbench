"""
Services package - Business logic layer.

This package contains all business logic services that coordinate
between API routes and CRUD operations.
"""

from app.services.document import DocumentService, DocumentNotFoundError
from app.services.llm import (
    LLMService,
    LLMServiceError,
    LLMAPIError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMConnectionError,
)
from app.services.embedding import (
    EmbeddingService,
    EmbeddingServiceError,
    EmbeddingAPIError,
    EmbeddingRateLimitError,
    EmbeddingTimeoutError,
    EmbeddingConnectionError,
    get_embedding_service,
)
from app.services.chunking import chunk_document, get_chunk_stats
from app.services.rag import RAGService, RAGServiceError, NoEmbeddingsFoundError

__all__ = [
    "DocumentService",
    "DocumentNotFoundError",
    "LLMService",
    "LLMServiceError",
    "LLMAPIError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMConnectionError",
    "EmbeddingService",
    "EmbeddingServiceError",
    "EmbeddingAPIError",
    "EmbeddingRateLimitError",
    "EmbeddingTimeoutError",
    "EmbeddingConnectionError",
    "get_embedding_service",
    "chunk_document",
    "get_chunk_stats",
    "RAGService",
    "RAGServiceError",
    "NoEmbeddingsFoundError",
]

