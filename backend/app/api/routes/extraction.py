"""
API routes for agent-based clinical data extraction.
"""

import logging
import time
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.extraction import ExtractionRequest, ExtractionResponse
from app.services.agent_extraction import get_extractor_service
from app.services.document import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/extract_structured",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract structured clinical data from medical note",
    description="""
    Extract structured clinical data from a medical note using an AI agent workflow.
    
    The agent will:
    1. Extract clinical entities (diagnoses, medications, vitals, labs, plans)
    2. Enrich diagnoses with ICD-10-CM codes (via NLM Clinical Tables API)
    3. Enrich medications with RxNorm codes (via NLM RxNav API)
    4. Return validated, structured data
    
    **Note:** This endpoint may take 30-60 seconds to process as the agent 
    makes multiple LLM and API calls.
    """,
    responses={
        200: {"description": "Successfully extracted structured data"},
        400: {"description": "Invalid request (empty or too short text)"},
        500: {"description": "Internal server error (agent execution failed)"},
    },
)
async def extract_structured_data(request: ExtractionRequest):
    """
    Extract structured clinical data from medical note using agent workflow.
    
    This endpoint uses an AI agent to:
    - Parse unstructured medical notes
    - Extract clinical entities (diagnoses, medications, vital signs, labs, plans)
    - Enrich diagnoses with ICD-10-CM codes
    - Enrich medications with RxNorm codes
    - Return structured, validated data
    
    Args:
        request: ExtractionRequest with note text
        
    Returns:
        ExtractionResponse with structured clinical data and metadata
        
    Raises:
        HTTPException: 400 if input is invalid, 500 if extraction fails
    """
    start_time = time.time()
    
    logger.info(f"Received extraction request (text length: {len(request.text)} chars)")
    
    try:
        # Get extractor service (singleton)
        extractor = get_extractor_service()
        
        # Run agent extraction
        structured_data = await extractor.extract_structured_data(request.text)
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Build response
        response = ExtractionResponse(
            **structured_data.model_dump(),
            processing_time_ms=processing_time_ms,
            model_used="gpt-4o-mini"
        )
        
        logger.info(
            f"Extraction successful: "
            f"{len(structured_data.diagnoses)} diagnoses, "
            f"{len(structured_data.medications)} medications, "
            f"processing time: {processing_time_ms}ms"
        )
        
        return response
        
    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent extraction failed: {str(e)}"
        )


@router.post(
    "/extract_document/{document_id}",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract structured clinical data from a document by ID",
    description="""
    Extract structured clinical data from a medical document by its ID.
    
    This endpoint fetches a document from the database and runs the same agent workflow as 
    `/extract_structured`:
    1. Extract clinical entities (diagnoses, medications, vitals, labs, plans)
    2. Enrich diagnoses with ICD-10-CM codes (via NLM Clinical Tables API)
    3. Enrich medications with RxNorm codes (via NLM RxNav API)
    4. Return validated, structured data
    
    **Note:** This endpoint may take 30-60 seconds to process as the agent 
    makes multiple LLM and API calls.
    """,
    responses={
        200: {"description": "Successfully extracted structured data"},
        404: {"description": "Document not found"},
        500: {"description": "Internal server error (agent execution failed)"},
    },
)
async def extract_document_data(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Extract structured clinical data from a document by ID using agent workflow.
    
    This endpoint fetches a document from the database and uses an AI agent to:
    - Parse unstructured medical notes
    - Extract clinical entities (diagnoses, medications, vital signs, labs, plans)
    - Enrich diagnoses with ICD-10-CM codes
    - Enrich medications with RxNorm codes
    - Return structured, validated data
    
    Args:
        document_id: ID of the document to extract data from
        db: Database session (injected)
        
    Returns:
        ExtractionResponse with structured clinical data and metadata
        
    Raises:
        HTTPException: 404 if document not found, 500 if extraction fails
    """
    start_time = time.time()
    
    logger.info(f"Received extraction request for document_id={document_id}")
    
    try:
        # Fetch document from database
        document = DocumentService.get_document_by_id(db, document_id)
        
        logger.info(
            f"Retrieved document: id={document.id}, title='{document.title}', "
            f"content_length={len(document.content)}"
        )
        
        # Get extractor service (singleton)
        extractor = get_extractor_service()
        
        # Run agent extraction on document content
        structured_data = await extractor.extract_structured_data(document.content)
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Build response
        response = ExtractionResponse(
            **structured_data.model_dump(),
            processing_time_ms=processing_time_ms,
            model_used="gpt-4o-mini"
        )
        
        logger.info(
            f"Extraction successful for document {document_id}: "
            f"{len(structured_data.diagnoses)} diagnoses, "
            f"{len(structured_data.medications)} medications, "
            f"processing time: {processing_time_ms}ms"
        )
        
        return response
        
    except ValueError as e:
        # Document not found or invalid content
        logger.warning(f"Invalid request for document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Extraction failed for document {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent extraction failed: {str(e)}"
        )
