"""
API routes for agent-based clinical data extraction.
"""

import logging
import time
from fastapi import APIRouter, HTTPException, status

from app.schemas.extraction import ExtractionRequest, ExtractionResponse
from app.services.agent_extraction import get_extractor_service

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


@router.get(
    "/health",
    summary="Health check for extraction service",
    description="Check if the extraction service is ready and initialized",
)
async def health_check():
    """
    Health check endpoint for the extraction service.
    
    Returns:
        dict with status and service info
    """
    try:
        # Verify service can be initialized
        extractor = get_extractor_service()
        return {
            "status": "ok",
            "service": "agent_extraction",
            "agent_name": extractor.agent.name,
            "tools_count": len(extractor.agent.tools)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}"
        )

