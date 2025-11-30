"""
Helper utilities for LLM route handlers.

This module provides reusable constants and decorators to reduce boilerplate
in LLM-related endpoints, including common response definitions and exception
handling logic.
"""

from functools import wraps
from typing import Callable, Any
import logging

from fastapi import HTTPException, status

from app.schemas.llm import SummarizeResponse, ErrorResponse
from app.services.llm import (
    LLMServiceError,
    LLMAPIError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMConnectionError,
    InvalidModelError,
)
from app.services.document import DocumentNotFoundError


logger = logging.getLogger(__name__)


# Common OpenAPI response definitions for LLM endpoints
COMMON_LLM_RESPONSES = {
    200: {
        "description": "Successfully generated summary",
        "model": SummarizeResponse,
    },
    400: {
        "description": "Invalid input (empty text, too short, etc.)",
        "model": ErrorResponse,
    },
    500: {
        "description": "Internal server error (LLM API error)",
        "model": ErrorResponse,
    },
    503: {
        "description": "Service unavailable (rate limit, timeout, connection error)",
        "model": ErrorResponse,
    },
}


# Response definitions that include 404 for document-based endpoints
DOCUMENT_LLM_RESPONSES = {
    **COMMON_LLM_RESPONSES,
    404: {
        "description": "Document not found",
        "model": ErrorResponse,
    },
}


def handle_llm_exceptions(func: Callable) -> Callable:
    """
    Decorator that handles common LLM service exceptions and converts them to HTTPExceptions.
    
    This decorator wraps endpoint functions and catches all common LLM-related exceptions,
    logging them appropriately and raising FastAPI HTTPException with proper status codes.
    
    Handles:
    - ValueError: 400 Bad Request (validation errors)
    - InvalidModelError: 400 Bad Request (unsupported model)
    - DocumentNotFoundError: 404 Not Found
    - LLMRateLimitError: 503 Service Unavailable
    - LLMTimeoutError: 503 Service Unavailable
    - LLMConnectionError: 503 Service Unavailable
    - LLMAPIError: 500 Internal Server Error
    - LLMServiceError: 500 Internal Server Error
    - Exception: 500 Internal Server Error (catch-all)
    
    Args:
        func: Async endpoint function to wrap
        
    Returns:
        Wrapped function with exception handling
        
    Example:
        ```python
        @router.post("/summarize")
        @handle_llm_exceptions
        async def summarize_note(request: SummarizeRequest):
            llm_service = get_llm_service()
            return llm_service.summarize_note(request.text)
        ```
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
            
        except ValueError as e:
            # Input validation errors (empty text, too short, etc.)
            logger.warning(f"Invalid input in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
            
        except InvalidModelError as e:
            # Invalid or unsupported model requested
            logger.warning(f"Invalid model in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
            
        except DocumentNotFoundError as e:
            # Document doesn't exist (for document-based endpoints)
            logger.warning(f"Document not found in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
            
        except LLMRateLimitError as e:
            # Rate limit exceeded
            logger.error(f"Rate limit error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI API rate limit exceeded. Please try again later."
            )
            
        except LLMTimeoutError as e:
            # Request timeout
            logger.error(f"Timeout error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Request to OpenAI API timed out. Please try again."
            )
            
        except LLMConnectionError as e:
            # Connection error
            logger.error(f"Connection error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to connect to OpenAI API. Please check your internet connection and try again."
            )
            
        except LLMAPIError as e:
            # OpenAI API error
            logger.error(f"OpenAI API error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OpenAI API error: {str(e)}"
            )
            
        except LLMServiceError as e:
            # General LLM service error
            logger.error(f"LLM service error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate summary: {str(e)}"
            )
            
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while processing your request."
            )
    
    return wrapper

