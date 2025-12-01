"""
API routes for FHIR conversion.
"""

import logging
import time
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status

from app.schemas.fhir import FHIRConversionRequest, FHIRConversionResponse
from app.services.fhir_conversion import get_fhir_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/convert",
    response_model=FHIRConversionResponse,
    status_code=status.HTTP_200_OK,
    summary="Convert structured clinical data to FHIR R4 resources",
    description="""
    Convert structured clinical data (from agent extraction) to FHIR R4-compliant resources.
    
    **Note:** You can directly copy the JSON response from the `/agent/extract_structured` 
    endpoint and use it as input here (just add a `patient_id` field if desired).
    
    **Conversions:**
    - patient_info → Patient (demographics)
    - diagnoses (with ICD-10-CM) → Condition (clinical conditions)
    - medications (with RxNorm) → MedicationRequest (medication orders)
    - vital_signs → Observation (vital-signs category with LOINC codes)
    - lab_results → Observation (laboratory category)
    
    **FHIR Compliance:**
    - Uses official fhir.resources library for R4 spec compliance
    - Includes standard coding systems: ICD-10-CM, RxNorm, LOINC
    - All clinical resources reference the patient
    """,
    responses={
        200: {"description": "Successfully converted to FHIR resources"},
        400: {"description": "Invalid structured data"},
        500: {"description": "FHIR conversion failed"},
    },
)
async def convert_to_fhir(request: FHIRConversionRequest) -> FHIRConversionResponse:
    """
    Convert structured clinical data to FHIR R4 resources.
    
    Takes the output from the agent extraction endpoint (Part 4) and converts
    it to FHIR-compliant JSON resources including Patient, Condition,
    MedicationRequest, and Observation.
    
    Args:
        request: FHIRConversionRequest with structured data and patient ID
        
    Returns:
        FHIRConversionResponse with FHIR resources and metadata
        
    Raises:
        HTTPException: 500 if conversion fails
    """
    start_time = time.time()
    
    logger.info(f"FHIR conversion request for patient: {request.patient_id}")
    
    try:
        # Get FHIR service (singleton)
        fhir_service = get_fhir_service()
        
        # Convert to FHIR (request extends StructuredClinicalData, so pass it directly)
        fhir_resources = fhir_service.convert_to_fhir(
            structured_data=request,
            patient_id=request.patient_id
        )
        
        # Calculate resource count
        resource_count = (
            (1 if fhir_resources["patient"] else 0) +
            len(fhir_resources["conditions"]) +
            len(fhir_resources["medications"]) +
            len(fhir_resources["observations"])
        )
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"FHIR conversion completed: {resource_count} resources, "
            f"{processing_time_ms}ms"
        )
        
        return FHIRConversionResponse(
            patient=fhir_resources["patient"],
            conditions=fhir_resources["conditions"],
            medications=fhir_resources["medications"],
            observations=fhir_resources["observations"],
            resource_count=resource_count,
            processing_time_ms=processing_time_ms
        )
        
    except Exception as e:
        logger.error(f"FHIR conversion failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"FHIR conversion failed: {str(e)}"
        )
