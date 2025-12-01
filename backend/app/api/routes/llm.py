"""
LLM operations endpoints.

Provides endpoints for LLM-powered medical document processing including
summarization and other text analysis tasks.
"""

from fastapi import APIRouter, status, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.schemas.llm import SummarizeRequest, SummarizeResponse
from app.services.llm import get_llm_service
from app.services.document import DocumentService
from app.api.routes.llm_helpers import (
    handle_llm_exceptions,
    COMMON_LLM_RESPONSES,
    DOCUMENT_LLM_RESPONSES,
)


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/summarize_note",
    response_model=SummarizeResponse,
    status_code=status.HTTP_200_OK,
    responses=COMMON_LLM_RESPONSES,
)
@handle_llm_exceptions
async def summarize_note(request: SummarizeRequest) -> SummarizeResponse:
    """
    Summarize a medical note using LLM.
    
    This endpoint takes a medical note (e.g., SOAP note) and generates a concise 
    summary highlighting key clinical information.

    Args:
        request: SummarizeRequest containing the medical note text
        
    Returns:
        SummarizeResponse with the summary and metadata
    """
    # Log incoming request
    logger.info(
        f"Received summarization request: text_length={len(request.text)}, "
        f"model_override={request.model}"
    )
    
    # Get singleton LLM service (initialized once, reused across all requests)
    llm_service = get_llm_service()
    
    # Call summarization method
    result = llm_service.summarize_note(
        text=request.text,
        model=request.model,
    )
    
    # Convert to response schema
    response = SummarizeResponse(
        summary=result["summary"],
        model_used=result["model_used"],
        token_usage=result["token_usage"],
        processing_time_ms=result["processing_time_ms"],
    )
    
    logger.info(
        f"Successfully generated summary: "
        f"summary_length={len(response.summary)}, "
        f"total_tokens={response.token_usage.total_tokens}"
    )
    
    return response


@router.post(
    "/summarize_document/{document_id}",
    response_model=SummarizeResponse,
    status_code=status.HTTP_200_OK,
    responses=DOCUMENT_LLM_RESPONSES,
)
@handle_llm_exceptions
async def summarize_document(
    document_id: int,
    model: Optional[str] = Query(
        None,
        description="Optional LLM model override (e.g., 'gpt-4o', 'gpt-5-nano'). Only OpenAI models supported.",
        examples=["gpt-5-nano", "gpt-5-mini", "gpt-4o"]
    ),
    db: Session = Depends(get_db)
) -> SummarizeResponse:
    """
    Summarize a medical document by ID using LLM with caching.
    
    This endpoint fetches a document from the database by its ID and generates
    a concise, accurate summary highlighting key clinical information.
    
    **Caching:** Summaries are cached to avoid redundant LLM API calls. If a cached 
    summary exists and the document hasn't been updated since the summary was generated, 
    the cached version is returned immediately. The response includes a `from_cache` 
    field to indicate whether the summary was retrieved from cache.
    
    **Note:** Only OpenAI models are supported. Other providers (Gemini, Claude, etc.) 
    are not supported. Invalid models will return a 400 error.
    
    Args:
        document_id: ID of the document to summarize
        model: Optional LLM model override (defaults to gpt-5-nano)
        db: Database session (injected)
        
    Returns:
        SummarizeResponse with the summary, metadata, and cache status
    """
    # Log incoming request
    logger.info(
        f"Received document summarization request: document_id={document_id}, "
        f"model_override={model}"
    )
    
    # Check cache first
    cached_result = DocumentService.check_summary_cache(db, document_id)
    
    if cached_result:
        # Return cached summary
        logger.info(f"Returning cached summary for document {document_id}")
        
        # Get token usage from cache or use defaults
        token_usage_dict = cached_result.get("token_usage", {})
        if not token_usage_dict or not isinstance(token_usage_dict, dict):
            token_usage_dict = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        # Ensure all required fields are present
        token_usage_dict.setdefault("prompt_tokens", 0)
        token_usage_dict.setdefault("completion_tokens", 0)
        token_usage_dict.setdefault("total_tokens", 0)
        
        response = SummarizeResponse(
            summary=cached_result["summary_text"],
            model_used=cached_result["model_used"] or "unknown",
            token_usage=token_usage_dict,
            processing_time_ms=0,  # No processing time for cached results
            from_cache=True
        )
        
        logger.info(f"Cache hit for document {document_id}")
        return response
    
    # Cache miss or stale cache - generate new summary
    logger.info(f"Cache miss for document {document_id} - generating new summary")
    
    # Fetch document from database
    document = DocumentService.get_document_by_id(db, document_id)
    
    logger.info(
        f"Retrieved document: id={document.id}, title='{document.title}', "
        f"content_length={len(document.content)}"
    )
    
    # Get singleton LLM service
    llm_service = get_llm_service()
    
    # Summarize document content
    result = llm_service.summarize_note(
        text=document.content,
        model=model,  # Pass model parameter
    )
    
    # Save to cache
    DocumentService.save_summary_cache(
        db=db,
        document_id=document_id,
        summary_text=result["summary"],
        model_used=result["model_used"],
        token_usage=result["token_usage"]
    )
    
    # Convert to response schema
    response = SummarizeResponse(
        summary=result["summary"],
        model_used=result["model_used"],
        token_usage=result["token_usage"],
        processing_time_ms=result["processing_time_ms"],
        from_cache=False
    )
    
    logger.info(
        f"Successfully summarized document {document_id}: "
        f"summary_length={len(response.summary)}, "
        f"total_tokens={response.token_usage.total_tokens}, "
        f"from_cache={response.from_cache}"
    )
    
    return response
