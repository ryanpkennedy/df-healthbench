"""
Service layer for LLM operations.

This module provides a clean interface for interacting with OpenAI's API,
handling API calls, error handling, logging, and response formatting.
"""

import logging
import time
from typing import Dict, Any, Optional
from openai import OpenAI, APIError, APIConnectionError, RateLimitError, APITimeoutError
from openai.types.chat import ChatCompletion

from app.config import settings


logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Base exception for LLM service errors."""
    pass


class LLMAPIError(LLMServiceError):
    """Raised when OpenAI API returns an error."""
    pass


class LLMRateLimitError(LLMServiceError):
    """Raised when OpenAI API rate limit is exceeded."""
    pass


class LLMTimeoutError(LLMServiceError):
    """Raised when OpenAI API request times out."""
    pass


class LLMConnectionError(LLMServiceError):
    """Raised when connection to OpenAI API fails."""
    pass


class LLMService:
    """
    Service class for LLM operations using OpenAI API.
    
    This class provides methods for interacting with OpenAI's language models,
    including medical note summarization and other text processing tasks.
    """
    
    def __init__(self):
        """
        Initialize the LLM service with OpenAI client.
        
        Raises:
            ValueError: If OPENAI_API_KEY is not configured
        """
        if not settings.openai_api_key:
            logger.error("OpenAI API key not configured")
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize OpenAI client
        client_kwargs = {
            "api_key": settings.openai_api_key,
            "timeout": settings.openai_timeout,
        }
        
        # Add project ID if configured
        # if settings.openai_api_project:
        #     logger.info(f"Using OpenAI Project ID: {settings.openai_api_project}")
        #     client_kwargs["project"] = settings.openai_api_project
        # else:
        #     logger.info("No OpenAI Project ID configured (using default project for API key)")
        
        self.client = OpenAI(**client_kwargs)
        
        # Store configuration
        self.default_model = settings.openai_default_model
        self.temperature = settings.openai_temperature
        
        logger.info(
            f"LLM service initialized with model={self.default_model}, "
            f"temperature={self.temperature}"
        )
    
    def _create_completion(
        self,
        messages: list[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> ChatCompletion:
        """
        Create a chat completion using OpenAI API.
        
        This is a private method that handles the actual API call with
        comprehensive error handling.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to configured model)
            temperature: Sampling temperature (defaults to configured value)
            
        Returns:
            ChatCompletion object from OpenAI
            
        Raises:
            LLMRateLimitError: If rate limit is exceeded
            LLMTimeoutError: If request times out
            LLMConnectionError: If connection fails
            LLMAPIError: For other API errors
        """
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.temperature
        
        # Log the request
        prompt_text = " ".join([m.get("content", "") for m in messages])
        prompt_length = len(prompt_text)
        logger.info(
            f"Creating completion: model={model}, temperature={temperature}, "
            f"prompt_length={prompt_length}"
        )
        
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Log success
            logger.info(
                f"Completion successful: model={response.model}, "
                f"completion_tokens={response.usage.completion_tokens}, "
                f"prompt_tokens={response.usage.prompt_tokens}, "
                f"total_tokens={response.usage.total_tokens}, "
                f"elapsed_time_ms={elapsed_time:.2f}"
            )
            
            return response
            
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {str(e)}")
            raise LLMRateLimitError(f"OpenAI API rate limit exceeded: {str(e)}") from e
            
        except APITimeoutError as e:
            logger.error(f"API request timeout: {str(e)}")
            raise LLMTimeoutError(f"OpenAI API request timed out: {str(e)}") from e
            
        except APIConnectionError as e:
            logger.error(f"API connection error: {str(e)}")
            raise LLMConnectionError(f"Failed to connect to OpenAI API: {str(e)}") from e
            
        except APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise LLMAPIError(f"OpenAI API error: {str(e)}") from e
            
        except Exception as e:
            logger.error(f"Unexpected error in LLM service: {str(e)}", exc_info=True)
            raise LLMServiceError(f"Unexpected error: {str(e)}") from e
    
    def summarize_note(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Summarize a medical note using LLM.
        
        This method takes a medical note (e.g., SOAP note) and generates
        a concise summary highlighting key clinical information.
        
        Args:
            text: The medical note text to summarize
            model: Optional model override (defaults to configured model)
            
        Returns:
            Dictionary containing:
                - summary: The generated summary text
                - model_used: The model that was used
                - token_usage: Token usage statistics
                - processing_time_ms: Processing time in milliseconds
                
        Raises:
            ValueError: If text is empty or too short
            LLMServiceError: For various API-related errors
            
        Example:
            >>> service = LLMService()
            >>> result = service.summarize_note("SOAP note content...")
            >>> print(result['summary'])
        """
        # Validation
        if not text or not text.strip():
            logger.warning("Attempted to summarize empty text")
            raise ValueError("Text cannot be empty")
        
        if len(text.strip()) < 10:
            logger.warning(f"Text too short for summarization: length={len(text)}")
            raise ValueError("Text must be at least 10 characters long")
        
        # Log the request
        logger.info(f"Summarizing medical note: text_length={len(text)}")
        
        # Create system and user messages
        system_prompt = """You are a medical documentation assistant specialized in summarizing clinical notes.

        Your task is to create a concise, accurate summary of medical notes that:
        1. Preserves all critical clinical information
        2. Maintains medical accuracy and terminology
        3. Highlights key findings, diagnoses, and treatment plans
        4. Organizes information clearly and logically
        5. Removes redundant or non-essential details

        Format your summary with clear sections when appropriate (e.g., Chief Complaint, Key Findings, Assessment, Plan).
        Keep the summary professional and suitable for healthcare providers."""

        user_prompt = f"""Please summarize the following medical note:

        {text}

        Provide a clear, concise summary that captures the essential clinical information."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        # Track processing time
        start_time = time.time()
        
        try:
            # Make API call
            response = self._create_completion(
                messages=messages,
                model=model,
            )
            
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Extract summary from response
            summary = response.choices[0].message.content
            
            if not summary:
                logger.error("OpenAI returned empty summary")
                raise LLMAPIError("Received empty response from OpenAI")
            
            # Build result
            result = {
                "summary": summary.strip(),
                "model_used": response.model,
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "processing_time_ms": int(processing_time),
            }
            
            logger.info(
                f"Successfully summarized note: "
                f"input_length={len(text)}, "
                f"summary_length={len(summary)}, "
                f"total_tokens={response.usage.total_tokens}"
            )
            
            return result
            
        except LLMServiceError:
            # Re-raise our custom exceptions
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error during summarization: {str(e)}", exc_info=True)
            raise LLMServiceError(f"Failed to summarize note: {str(e)}") from e


# Singleton instance management
_llm_service_instance: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """
    Get or create the singleton LLM service instance.
    
    This ensures only one LLMService (and thus one OpenAI client) is created
    and reused across all requests, improving performance through connection
    pooling and reducing initialization overhead.
    
    The singleton pattern is thread-safe for our use case because:
    - The OpenAI client is thread-safe
    - Each request has its own data (text, results, etc.)
    - No shared mutable state between requests
    
    Returns:
        LLMService: Singleton instance of the LLM service
        
    Example:
        >>> llm_service = get_llm_service()
        >>> result = llm_service.summarize_note("Patient note...")
    """
    global _llm_service_instance
    
    if _llm_service_instance is None:
        logger.info("Initializing singleton LLM service")
        _llm_service_instance = LLMService()
    
    return _llm_service_instance
