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
    Summarize a medical document by ID using LLM.
    
    This endpoint fetches a document from the database by its ID and generates
    a concise, accurate summary highlighting key clinical information.
    
    **Note:** Only OpenAI models are supported. Other providers (Gemini, Claude, etc.) 
    are not supported. Invalid models will return a 400 error.
    
    Args:
        document_id: ID of the document to summarize
        model: Optional LLM model override (defaults to gpt-5-nano)
        db: Database session (injected)
        
    Returns:
        SummarizeResponse with the summary and metadata
    """
    # Log incoming request
    logger.info(
        f"Received document summarization request: document_id={document_id}, "
        f"model_override={model}"
    )
    
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
    
    # Convert to response schema
    response = SummarizeResponse(
        summary=result["summary"],
        model_used=result["model_used"],
        token_usage=result["token_usage"],
        processing_time_ms=result["processing_time_ms"],
    )
    
    logger.info(
        f"Successfully summarized document {document_id}: "
        f"summary_length={len(response.summary)}, "
        f"total_tokens={response.token_usage.total_tokens}"
    )
    
    return response
