"""
Pydantic schemas for agent-based clinical data extraction.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PatientInfo(BaseModel):
    """Patient demographic information."""
    age: Optional[str] = None
    gender: Optional[str] = None


class VitalSigns(BaseModel):
    """Patient vital signs extracted from note."""
    temperature: Optional[str] = None
    blood_pressure: Optional[str] = None
    heart_rate: Optional[str] = None
    respiratory_rate: Optional[str] = None
    oxygen_saturation: Optional[str] = None
    weight: Optional[str] = None
    height: Optional[str] = None
    bmi: Optional[str] = None


class DiagnosisCode(BaseModel):
    """Diagnosis with ICD-10-CM code enrichment."""
    text: str = Field(description="Original diagnosis text from note")
    icd10_code: Optional[str] = Field(None, description="ICD-10-CM code")
    icd10_description: Optional[str] = Field(None, description="ICD-10-CM code description")
    confidence: Optional[str] = Field(None, description="Confidence level: exact, high, low, or none")


class MedicationCode(BaseModel):
    """Medication with RxNorm code enrichment."""
    text: str = Field(description="Original medication text from note")
    rxnorm_code: Optional[str] = Field(None, description="RxNorm RxCUI")
    rxnorm_name: Optional[str] = Field(None, description="RxNorm normalized name")
    confidence: Optional[str] = Field(None, description="Confidence level: exact, approximate, or none")


class StructuredClinicalData(BaseModel):
    """Final structured output from agent."""
    patient_info: Optional[PatientInfo] = Field(None, description="Patient demographics if available")
    diagnoses: List[DiagnosisCode] = Field(default_factory=list, description="Conditions and diagnoses with ICD codes")
    medications: List[MedicationCode] = Field(default_factory=list, description="Medications with RxNorm codes")
    vital_signs: Optional[VitalSigns] = Field(None, description="Vital signs")
    lab_results: List[str] = Field(default_factory=list, description="Laboratory test results")
    plan_actions: List[str] = Field(default_factory=list, description="Treatment plan and follow-up actions")


# ============================================================================
# API Request/Response Schemas
# ============================================================================


class ExtractionRequest(BaseModel):
    """Request schema for clinical data extraction."""
    text: str = Field(..., description="Raw medical note text to extract data from", min_length=10)
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Subjective: 45yo male with Type 2 Diabetes Mellitus presents for follow-up.\n\nObjective: BP 130/85, HR 72, Temp 98.6°F.\n\nAssessment: Type 2 Diabetes Mellitus, well-controlled.\n\nPlan: Continue Metformin 500mg twice daily. Follow-up in 3 months."
            }
        }


class ExtractionResponse(StructuredClinicalData):
    """Response schema for clinical data extraction with metadata."""
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    model_used: str = Field(default="gpt-4o-mini", description="LLM model used for extraction")
    
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
                        "text": "Metformin 500mg twice daily",
                        "rxnorm_code": "860975",
                        "rxnorm_name": "Metformin 500 MG Oral Tablet",
                        "confidence": "exact"
                    }
                ],
                "vital_signs": {
                    "blood_pressure": "130/85",
                    "heart_rate": "72",
                    "temperature": "98.6°F",
                    "respiratory_rate": None,
                    "oxygen_saturation": None,
                    "weight": None,
                    "height": None,
                    "bmi": None
                },
                "lab_results": [],
                "plan_actions": [
                    "Continue Metformin 500mg twice daily",
                    "Follow-up in 3 months"
                ],
                "processing_time_ms": 5432,
                "model_used": "gpt-4o-mini"
            }
        }

