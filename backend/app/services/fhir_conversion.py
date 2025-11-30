"""
FHIR R4 conversion service for structured clinical data.

Converts structured clinical data (extracted by the agent) into FHIR R4-compliant
resources including Patient, Condition, MedicationRequest, and Observation.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from fhir.resources.patient import Patient
from fhir.resources.condition import Condition
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.observation import Observation
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.codeablereference import CodeableReference
from fhir.resources.coding import Coding

from app.schemas.extraction import (
    StructuredClinicalData,
    DiagnosisCode,
    MedicationCode,
    VitalSigns,
    PatientInfo,
)

logger = logging.getLogger(__name__)


class FHIRConversionService:
    """
    Service class for converting structured clinical data to FHIR R4 resources.
    
    This service maps structured data (with ICD-10-CM and RxNorm codes) to
    FHIR-compliant resources for interoperability with healthcare systems.
    """
    
    def __init__(self):
        """Initialize the FHIR conversion service."""
        logger.info("FHIR conversion service initialized")
    
    def convert_to_fhir(
        self,
        structured_data: StructuredClinicalData,
        patient_id: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Convert structured clinical data to FHIR R4 resources.
        
        Args:
            structured_data: Structured clinical data from agent extraction
            patient_id: Patient identifier (defaults to "unknown")
        
        Returns:
            Dict with:
            - patient: Patient resource (or None)
            - conditions: List of Condition resources
            - medications: List of MedicationRequest resources
            - observations: List of Observation resources (vitals + labs)
        """
        logger.info(f"Converting structured data to FHIR for patient: {patient_id}")
        
        result = {
            "patient": None,
            "conditions": [],
            "medications": [],
            "observations": []
        }
        
        # 1. Convert patient info
        if structured_data.patient_info:
            patient = self.map_patient_info_to_fhir(
                structured_data.patient_info,
                patient_id
            )
            if patient:
                result["patient"] = patient.model_dump(mode='json')
        
        # 2. Convert diagnoses to Conditions
        for diagnosis in structured_data.diagnoses:
            condition = self.map_diagnosis_to_condition(diagnosis, patient_id)
            result["conditions"].append(condition.model_dump(mode='json'))
        
        # 3. Convert medications to MedicationRequests
        for medication in structured_data.medications:
            med_request = self.map_medication_to_request(medication, patient_id)
            result["medications"].append(med_request.model_dump(mode='json'))
        
        # 4. Convert vital signs to Observations
        if structured_data.vital_signs:
            vital_obs = self.map_vital_signs_to_observations(
                structured_data.vital_signs,
                patient_id
            )
            result["observations"].extend([obs.model_dump(mode='json') for obs in vital_obs])
        
        # 5. Convert lab results to Observations (simplified text-only)
        for idx, lab_text in enumerate(structured_data.lab_results):
            obs = self.map_lab_result_to_observation(lab_text, patient_id, idx)
            result["observations"].append(obs.model_dump(mode='json'))
        
        logger.info(
            f"FHIR conversion complete: {len(result['conditions'])} conditions, "
            f"{len(result['medications'])} medications, "
            f"{len(result['observations'])} observations"
        )
        
        return result
    
    def map_patient_info_to_fhir(
        self,
        patient_info: Optional[PatientInfo],
        patient_id: str
    ) -> Optional[Patient]:
        """
        Map PatientInfo to FHIR Patient resource.
        
        Args:
            patient_info: Patient demographics from extraction
            patient_id: Patient identifier
        
        Returns:
            FHIR Patient resource or None if no patient info available
        """
        if not patient_info or (not patient_info.age and not patient_info.gender):
            return None
        
        patient_data = {
            "resourceType": "Patient",
            "id": patient_id,
            "identifier": [{
                "system": "urn:oid:df-healthbench",
                "value": patient_id
            }]
        }
        
        # Map gender
        if patient_info.gender:
            gender_map = {
                "male": "male",
                "female": "female",
                "m": "male",
                "f": "female"
            }
            patient_data["gender"] = gender_map.get(
                patient_info.gender.lower(),
                "unknown"
            )
        
        # Derive birthDate from age (approximate)
        if patient_info.age:
            try:
                age_int = int(patient_info.age)
                birth_year = datetime.now().year - age_int
                patient_data["birthDate"] = f"{birth_year}-01-01"
            except ValueError:
                logger.warning(f"Could not parse age: {patient_info.age}")
        
        return Patient(**patient_data)
    
    def map_diagnosis_to_condition(
        self,
        diagnosis: DiagnosisCode,
        patient_id: str
    ) -> Condition:
        """
        Map DiagnosisCode to FHIR Condition resource.
        
        Args:
            diagnosis: Diagnosis with ICD-10-CM code
            patient_id: Patient identifier
        
        Returns:
            FHIR Condition resource
        """
        # Build coding array
        coding_list = []
        if diagnosis.icd10_code:
            coding_list.append({
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "code": diagnosis.icd10_code,
                "display": diagnosis.icd10_description or diagnosis.text
            })
        
        condition_data = {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active"
                }]
            },
            "verificationStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed"
                }]
            },
            "code": {
                "coding": coding_list if coding_list else None,
                "text": diagnosis.text
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "recordedDate": datetime.now(timezone.utc).isoformat()
        }
        
        return Condition(**condition_data)
    
    def map_medication_to_request(
        self,
        medication: MedicationCode,
        patient_id: str
    ) -> MedicationRequest:
        """
        Map MedicationCode to FHIR MedicationRequest resource.
        
        Args:
            medication: Medication with RxNorm code
            patient_id: Patient identifier
        
        Returns:
            FHIR MedicationRequest resource
        """
        # Build coding array
        coding_list = []
        if medication.rxnorm_code:
            coding_list.append(
                Coding(
                    system="http://www.nlm.nih.gov/research/umls/rxnorm",
                    code=medication.rxnorm_code,
                    display=medication.rxnorm_name or medication.text
                )
            )
        
        # Create CodeableConcept for medication
        medication_concept = CodeableConcept(
            coding=coding_list if coding_list else None,
            text=medication.text
        )
        
        # Wrap in CodeableReference (required by FHIR)
        medication_ref = CodeableReference(
            concept=medication_concept
        )
        
        med_request_data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medication": medication_ref,
            "subject": {"reference": f"Patient/{patient_id}"},
            "authoredOn": datetime.now(timezone.utc).isoformat()
        }
        
        return MedicationRequest(**med_request_data)
    
    def map_vital_signs_to_observations(
        self,
        vital_signs: Optional[VitalSigns],
        patient_id: str
    ) -> List[Observation]:
        """
        Map VitalSigns to FHIR Observation resources.
        
        Creates one Observation per vital sign with LOINC codes.
        
        Args:
            vital_signs: Vital signs from extraction
            patient_id: Patient identifier
        
        Returns:
            List of FHIR Observation resources
        """
        if not vital_signs:
            return []
        
        observations = []
        
        # LOINC code mapping for common vitals
        vital_mappings = {
            "blood_pressure": ("85354-9", "Blood pressure panel"),
            "heart_rate": ("8867-4", "Heart rate"),
            "respiratory_rate": ("9279-1", "Respiratory rate"),
            "temperature": ("8310-5", "Body temperature"),
            "oxygen_saturation": ("2708-6", "Oxygen saturation"),
            "weight": ("29463-7", "Body weight"),
            "height": ("8302-2", "Body height"),
            "bmi": ("39156-5", "Body mass index")
        }
        
        for field_name, (loinc_code, display) in vital_mappings.items():
            value = getattr(vital_signs, field_name, None)
            if value:
                obs_data = {
                    "resourceType": "Observation",
                    "status": "final",
                    "category": [{
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "vital-signs"
                        }]
                    }],
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": loinc_code,
                            "display": display
                        }],
                        "text": display
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "effectiveDateTime": datetime.now(timezone.utc).isoformat(),
                    "valueString": str(value)  # Simplified - using string for all values
                }
                observations.append(Observation(**obs_data))
        
        return observations
    
    def map_lab_result_to_observation(
        self,
        lab_text: str,
        patient_id: str,
        index: int
    ) -> Observation:
        """
        Map lab result text to FHIR Observation resource.
        
        Args:
            lab_text: Lab result text
            patient_id: Patient identifier
            index: Lab result index (for uniqueness)
        
        Returns:
            FHIR Observation resource
        """
        obs_data = {
            "resourceType": "Observation",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory"
                }]
            }],
            "code": {"text": "Laboratory result"},
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": datetime.now(timezone.utc).isoformat(),
            "valueString": lab_text
        }
        
        return Observation(**obs_data)


# ============================================================================
# Singleton Pattern
# ============================================================================

_fhir_service_instance: Optional[FHIRConversionService] = None


def get_fhir_service() -> FHIRConversionService:
    """
    Get or create singleton FHIR conversion service instance.
    
    Returns:
        FHIRConversionService: Singleton service instance
    """
    global _fhir_service_instance
    if _fhir_service_instance is None:
        _fhir_service_instance = FHIRConversionService()
        logger.info("FHIR conversion service singleton created")
    return _fhir_service_instance

