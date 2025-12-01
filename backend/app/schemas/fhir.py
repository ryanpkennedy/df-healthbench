"""
Pydantic schemas for FHIR conversion API.
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

from app.schemas.extraction import StructuredClinicalData


class FHIRConversionRequest(StructuredClinicalData):
    """
    Request schema for FHIR conversion.
    
    This schema extends StructuredClinicalData and matches the structure of 
    ExtractionResponse, allowing you to directly pass the extraction endpoint's
    response as input to the FHIR conversion endpoint.
    """
    
    # Optional metadata fields from ExtractionResponse (ignored during conversion)
    processing_time_ms: Optional[int] = Field(
        None,
        description="Processing time from extraction (optional, will be ignored)"
    )
    model_used: Optional[str] = Field(
        None,
        description="Model used for extraction (optional, will be ignored)"
    )
    
    # Patient identifier for FHIR resources
    patient_id: Optional[str] = Field(
        default="unknown",
        description="Patient identifier (if known)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "patient_info": {
                    "age": "45",
                    "gender": "male"
                },
                "diagnoses": [
                    {
                        "text": "Type 2 Diabetes Mellitus",
                        "icd10_code": "E11.9",
                        "icd10_description": "Type 2 diabetes mellitus without complications",
                        "confidence": "exact"
                    }
                ],
                "medications": [
                    {
                        "text": "Metformin 500mg",
                        "rxnorm_code": "860975",
                        "rxnorm_name": "Metformin 500 MG Oral Tablet",
                        "confidence": "exact"
                    }
                ],
                "vital_signs": {
                    "blood_pressure": "130/85",
                    "heart_rate": "72",
                    "temperature": "98.6°F"
                },
                "lab_results": ["HbA1c: 7.2%"],
                "plan_actions": ["Continue current medications"],
                "patient_id": "patient-123",
                "processing_time_ms": 5432,
                "model_used": "gpt-4o-mini"
            }
        }


class FHIRConversionResponse(BaseModel):
    """Response schema containing FHIR resources."""
    
    patient: Optional[Dict[str, Any]] = Field(
        None,
        description="FHIR Patient resource"
    )
    conditions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="FHIR Condition resources"
    )
    medications: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="FHIR MedicationRequest resources"
    )
    observations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="FHIR Observation resources (vitals + labs)"
    )
    resource_count: int = Field(
        ...,
        description="Total number of FHIR resources created"
    )
    processing_time_ms: int = Field(
        ...,
        description="Processing time in milliseconds"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "patient": {
                    "resourceType": "Patient",
                    "id": "patient-123",
                    "gender": "male",
                    "birthDate": "1978-01-01"
                },
                "conditions": [
                    {
                        "resourceType": "Condition",
                        "clinicalStatus": {
                            "coding": [{
                                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": "active"
                            }]
                        },
                        "code": {
                            "coding": [{
                                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                                "code": "E11.9",
                                "display": "Type 2 diabetes mellitus without complications"
                            }],
                            "text": "Type 2 Diabetes Mellitus"
                        },
                        "subject": {"reference": "Patient/patient-123"}
                    }
                ],
                "medications": [
                    {
                        "resourceType": "MedicationRequest",
                        "status": "active",
                        "intent": "order",
                        "medication": {
                            "concept": {
                                "coding": [{
                                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                    "code": "860975",
                                    "display": "Metformin 500 MG Oral Tablet"
                                }],
                                "text": "Metformin 500mg"
                            }
                        },
                        "subject": {"reference": "Patient/patient-123"}
                    }
                ],
                "observations": [],
                "resource_count": 8,
                "processing_time_ms": 145
            }
        }

