"""
Service layer for embedding operations.

This module provides a clean interface for generating text embeddings using
OpenAI's embedding models, handling API calls, error handling, and batch processing.
"""

import logging
import time
from typing import List, Optional
from openai import OpenAI, APIError, APIConnectionError, RateLimitError, APITimeoutError

from app.config import settings


logger = logging.getLogger(__name__)


class EmbeddingServiceError(Exception):
    """Base exception for embedding service errors."""
    pass


class EmbeddingAPIError(EmbeddingServiceError):
    """Raised when OpenAI API returns an error."""
    pass


class EmbeddingRateLimitError(EmbeddingServiceError):
    """Raised when OpenAI API rate limit is exceeded."""
    pass


class EmbeddingTimeoutError(EmbeddingServiceError):
    """Raised when OpenAI API request times out."""
    pass


class EmbeddingConnectionError(EmbeddingServiceError):
    """Raised when connection to OpenAI API fails."""
    pass


class EmbeddingService:
    """
    Service class for generating text embeddings using OpenAI API.
    
    This class provides methods for generating embeddings for text chunks,
    with support for both single and batch operations.
    
    Uses text-embedding-3-small model:
    - 1536 dimensions
    - $0.02 per 1M tokens (cost-effective)
    - Fast inference
    - Sufficient quality for medical document retrieval
    """
    
    def __init__(self):
        """
        Initialize the Embedding service with OpenAI client.
        
        Raises:
            ValueError: If OPENAI_API_KEY is not configured
        """
        if not settings.openai_api_key:
            logger.error("OpenAI API key not configured")
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize OpenAI client (reuse from settings)
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout,
        )
        
        # Store configuration
        self.embedding_model = settings.openai_embedding_model
        self.embedding_dimension = settings.embedding_dimension
        
        logger.info(
            f"Embedding service initialized with model={self.embedding_model}, "
            f"dimensions={self.embedding_dimension}"
        )
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for a single text string.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector (1536 dimensions)
            
        Raises:
            ValueError: If text is empty
            EmbeddingServiceError: For various API-related errors
            
        Example:
            >>> service = EmbeddingService()
            >>> embedding = service.generate_embedding("Patient has diabetes")
            >>> len(embedding)
            1536
        """
        if not text or not text.strip():
            logger.warning("Attempted to embed empty text")
            raise ValueError("Text cannot be empty")
        
        logger.debug(f"Generating embedding for text: length={len(text)}")
        
        start_time = time.time()
        
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )
            
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
            
            embedding = response.data[0].embedding
            
            logger.debug(
                f"Embedding generated: dimensions={len(embedding)}, "
                f"elapsed_time_ms={elapsed_time:.2f}"
            )
            
            return embedding
            
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {str(e)}")
            raise EmbeddingRateLimitError(f"OpenAI API rate limit exceeded: {str(e)}") from e
            
        except APITimeoutError as e:
            logger.error(f"API request timeout: {str(e)}")
            raise EmbeddingTimeoutError(f"OpenAI API request timed out: {str(e)}") from e
            
        except APIConnectionError as e:
            logger.error(f"API connection error: {str(e)}")
            raise EmbeddingConnectionError(f"Failed to connect to OpenAI API: {str(e)}") from e
            
        except APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise EmbeddingAPIError(f"OpenAI API error: {str(e)}") from e
            
        except Exception as e:
            logger.error(f"Unexpected error in embedding service: {str(e)}", exc_info=True)
            raise EmbeddingServiceError(f"Unexpected error: {str(e)}") from e
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a single API call.
        
        This is more efficient than calling generate_embedding() multiple times
        as it uses OpenAI's batch embedding endpoint.
        
        Args:
            texts: List of text strings to embed (max 100 per batch)
            
        Returns:
            List of embedding vectors, one per input text
            
        Raises:
            ValueError: If texts list is empty or exceeds batch size
            EmbeddingServiceError: For various API-related errors
            
        Example:
            >>> service = EmbeddingService()
            >>> chunks = ["Patient has diabetes", "Blood pressure is elevated"]
            >>> embeddings = service.generate_embeddings_batch(chunks)
            >>> len(embeddings)
            2
            >>> len(embeddings[0])
            1536
        """
        if not texts:
            logger.warning("Attempted to embed empty text list")
            raise ValueError("Texts list cannot be empty")
        
        # Filter out empty strings
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            logger.warning("All texts in batch were empty")
            raise ValueError("All texts in batch are empty")
        
        if len(valid_texts) > 100:
            logger.warning(f"Batch size {len(valid_texts)} exceeds recommended limit of 100")
            raise ValueError("Batch size cannot exceed 100 texts")
        
        logger.info(f"Generating embeddings for batch: size={len(valid_texts)}")
        
        start_time = time.time()
        
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=valid_texts,
            )
            
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Extract embeddings in order
            embeddings = [item.embedding for item in response.data]
            
            logger.info(
                f"Batch embeddings generated: count={len(embeddings)}, "
                f"dimensions={len(embeddings[0])}, "
                f"elapsed_time_ms={elapsed_time:.2f}"
            )
            
            return embeddings
            
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {str(e)}")
            raise EmbeddingRateLimitError(f"OpenAI API rate limit exceeded: {str(e)}") from e
            
        except APITimeoutError as e:
            logger.error(f"API request timeout: {str(e)}")
            raise EmbeddingTimeoutError(f"OpenAI API request timed out: {str(e)}") from e
            
        except APIConnectionError as e:
            logger.error(f"API connection error: {str(e)}")
            raise EmbeddingConnectionError(f"Failed to connect to OpenAI API: {str(e)}") from e
            
        except APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise EmbeddingAPIError(f"OpenAI API error: {str(e)}") from e
            
        except Exception as e:
            logger.error(f"Unexpected error in embedding service: {str(e)}", exc_info=True)
            raise EmbeddingServiceError(f"Unexpected error: {str(e)}") from e


# Singleton instance management
_embedding_service_instance: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get or create the singleton Embedding service instance.
    
    This ensures only one EmbeddingService (and thus one OpenAI client) is created
    and reused across all requests, improving performance through connection
    pooling and reducing initialization overhead.
    
    The singleton pattern is thread-safe for our use case because:
    - The OpenAI client is thread-safe
    - Each request has its own data (text, embeddings, etc.)
    - No shared mutable state between requests
    
    Returns:
        EmbeddingService: Singleton instance of the Embedding service
        
    Example:
        >>> embedding_service = get_embedding_service()
        >>> embedding = embedding_service.generate_embedding("Patient note...")
    """
    global _embedding_service_instance
    
    if _embedding_service_instance is None:
        logger.info("Initializing singleton Embedding service")
        _embedding_service_instance = EmbeddingService()
    
    return _embedding_service_instance

