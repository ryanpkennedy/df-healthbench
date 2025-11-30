# Sprint Plan 5: FHIR Conversion

**Estimated Time:** 2 hours  
**Goal:** Convert structured clinical data from Part 4 (agent extraction) into FHIR R4-compliant resources

---

## Overview

This sprint implements Part 5 of the project: converting structured clinical data (extracted by the agent in Part 4) into FHIR-compatible JSON format.

**What We're Converting:**

- **Input:** `StructuredClinicalData` (from Part 4) containing diagnoses with ICD-10-CM codes, medications with RxNorm codes, vital signs, lab results, and patient info
- **Output:** FHIR R4 resources (Patient, Condition, MedicationRequest, Observation)

**Key Technologies:**

- **fhir.resources**: Official Python FHIR library for R4 spec compliance
- **Pydantic**: Already used for validation (fhir.resources is Pydantic-based)
- **FastAPI**: New endpoint for FHIR conversion

**Architecture Approach:**

1. **Install FHIR library** (Phase 1): Use `fhir.resources` for spec compliance
2. **Prototype in Notebook** (Phase 2-3): Develop and test FHIR mapping functions interactively
3. **Integrate into Backend** (Phase 4-5): Convert notebook code to service layer + API endpoint
4. **Test & document** (Phase 6): Validate with SOAP notes

**Why Notebook First?** (Same approach as Sprint 4)

- ✅ Interactive development and testing of FHIR mapping functions
- ✅ Easy to iterate on resource structure and field mappings
- ✅ Can visualize FHIR output before committing to API structure
- ✅ Reuse existing agent extraction results from notebook
- ✅ Test individual mapping functions independently
- ✅ Fast feedback loop for FHIR validation

---

## Phase 1: Setup & Dependencies (Notebook) (10 minutes)

### 1.1 Install FHIR Resources Library

**Add to Poetry dependencies:**

```bash
cd backend
poetry add fhir.resources
```

**Why `fhir.resources`?**

- ✅ Official Python FHIR R4 library
- ✅ Pydantic-based validation (already familiar from project)
- ✅ Full spec compliance with all resource types
- ✅ Serialize to/from JSON automatically
- ✅ Well-maintained and documented

**Estimated time:** 3 minutes

---

### 1.2 Add Notebook Section for FHIR Conversion

**File:** `backend/notebooks/agent_extraction_prototype.ipynb`

**Add new markdown cell at bottom:**

```markdown
## Section 6: FHIR Conversion

Now that we have structured clinical data with ICD-10-CM and RxNorm codes,
let's convert it to FHIR R4 resources.
```

**Add new code cell - Test imports:**

```python
# FHIR resource imports
from fhir.resources.patient import Patient
from fhir.resources.condition import Condition
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.observation import Observation
from fhir.resources.bundle import Bundle
from datetime import datetime

print("✅ FHIR resources library imported successfully")
```

**Estimated time:** 5 minutes

---

### 1.3 Review Available Data

**We already have extracted structured data from previous notebook cells:**

- Variable: `structured_data` (from the agent extraction)
- Contains: `patient_info`, `diagnoses` (with ICD-10-CM codes), `medications` (with RxNorm codes), `vital_signs`, `lab_results`, `plan_actions`

**Quick validation cell:**

```python
# Verify we have data to work with
print("Available data from agent extraction:")
print(f"  • Patient info: {structured_data.patient_info is not None}")
print(f"  • Diagnoses: {len(structured_data.diagnoses)}")
print(f"  • Medications: {len(structured_data.medications)}")
print(f"  • Vital signs: {structured_data.vital_signs is not None}")
print(f"  • Lab results: {len(structured_data.lab_results)}")
print(f"  • Plan actions: {len(structured_data.plan_actions)}")
```

**Estimated time:** 2 minutes

---

## Phase 2: FHIR Mapping Functions (Notebook) (30 minutes)

### 2.1 Design Mapping Strategy (Notebook Cell)

**Add markdown cell explaining the mapping approach:**

```markdown
### FHIR Mapping Strategy

We'll convert our structured data to these FHIR R4 resources:

| Extracted Data | FHIR Resource      | Key Fields                                     |
| -------------- | ------------------ | ---------------------------------------------- |
| `patient_info` | Patient            | gender, age (derive birthDate), identifier     |
| `diagnoses`    | Condition (list)   | code (ICD-10-CM), clinicalStatus, subject      |
| `medications`  | MedicationRequest  | medicationCodeableConcept (RxNorm), subject    |
| `vital_signs`  | Observation (list) | code (LOINC), value, subject, category="vital" |
| `lab_results`  | Observation (list) | code (text), value (text), category="lab"      |

**Design decisions:**

- Use "patient-soap-01" as patient ID
- All conditions are "active" and "confirmed" (simplified)
- Use ICD-10-CM system for diagnoses
- Use RxNorm system for medications
- Use LOINC codes for vital signs
- Text-only codes for lab results
```

**Estimated time:** 3 minutes

---

### 2.2 Implement Patient Mapping (Notebook Cell)

**Add code cell:**

```python
def map_patient_info_to_fhir(patient_info, patient_id: str = "unknown"):
    """
    Map PatientInfo to FHIR Patient resource.

    Returns None if no patient info available.
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
        gender_map = {"male": "male", "female": "female", "m": "male", "f": "female"}
        patient_data["gender"] = gender_map.get(patient_info.gender.lower(), "unknown")

    # Derive birthDate from age (approximate)
    if patient_info.age:
        try:
            age_int = int(patient_info.age)
            birth_year = datetime.now().year - age_int
            patient_data["birthDate"] = f"{birth_year}-01-01"
        except ValueError:
            print(f"Warning: Could not parse age: {patient_info.age}")

    return Patient(**patient_data)

# Test with our data
patient_resource = map_patient_info_to_fhir(structured_data.patient_info, "patient-soap-01")
if patient_resource:
    print("✅ Patient resource created:")
    print(json.dumps(patient_resource.dict(), indent=2))
else:
    print("ℹ️  No patient info to convert")
```

**Estimated time:** 7 minutes

---

### 2.3 Implement Condition Mapping (Notebook Cell)

**Add code cell:**

```python
def map_diagnosis_to_condition(diagnosis, patient_id: str):
    """
    Map DiagnosisCode to FHIR Condition resource.

    Uses ICD-10-CM code if available.
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
        "recordedDate": datetime.now().isoformat()
    }

    return Condition(**condition_data)

# Test with first diagnosis
if structured_data.diagnoses:
    condition = map_diagnosis_to_condition(structured_data.diagnoses[0], "patient-soap-01")
    print("✅ Condition resource created:")
    print(json.dumps(condition.dict(), indent=2))
else:
    print("ℹ️  No diagnoses to convert")
```

**Estimated time:** 7 minutes

---

### 2.4 Implement MedicationRequest Mapping (Notebook Cell)

**Add code cell:**

```python
def map_medication_to_request(medication, patient_id: str):
    """
    Map MedicationCode to FHIR MedicationRequest resource.

    Uses RxNorm code if available.
    """
    # Build coding array
    coding_list = []
    if medication.rxnorm_code:
        coding_list.append({
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "code": medication.rxnorm_code,
            "display": medication.rxnorm_name or medication.text
        })

    med_request_data = {
        "resourceType": "MedicationRequest",
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {
            "coding": coding_list if coding_list else None,
            "text": medication.text
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "authoredOn": datetime.now().isoformat()
    }

    return MedicationRequest(**med_request_data)

# Test with first medication
if structured_data.medications:
    med_request = map_medication_to_request(structured_data.medications[0], "patient-soap-01")
    print("✅ MedicationRequest resource created:")
    print(json.dumps(med_request.dict(), indent=2))
else:
    print("ℹ️  No medications to convert")
```

**Estimated time:** 6 minutes

---

### 2.5 Implement Observation Mapping (Notebook Cell)

**Add code cell:**

```python
def map_vital_signs_to_observations(vital_signs, patient_id: str):
    """
    Map VitalSigns to FHIR Observation resources.

    Creates one Observation per vital with LOINC codes.
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
                "effectiveDateTime": datetime.now().isoformat(),
                "valueString": str(value)  # Simplified
            }
            observations.append(Observation(**obs_data))

    return observations

# Test with vital signs
vital_observations = map_vital_signs_to_observations(
    structured_data.vital_signs,
    "patient-soap-01"
)
print(f"✅ Created {len(vital_observations)} vital sign Observations")
if vital_observations:
    print("\nFirst vital observation:")
    print(json.dumps(vital_observations[0].dict(), indent=2))
```

**Estimated time:** 7 minutes

---

## Phase 3: Test Full FHIR Conversion (Notebook) (15 minutes)

### 3.1 Create Main Conversion Function (Notebook Cell)

**Add code cell to orchestrate all mappings:**

```python
def convert_to_fhir(structured_data, patient_id: str = "unknown"):
    """
    Convert structured clinical data to FHIR R4 resources.

    Returns dict with patient, conditions, medications, observations.
    """
    result = {
        "patient": None,
        "conditions": [],
        "medications": [],
        "observations": []
    }

    # 1. Convert patient
    if structured_data.patient_info:
        patient = map_patient_info_to_fhir(structured_data.patient_info, patient_id)
        if patient:
            result["patient"] = patient.dict()

    # 2. Convert diagnoses to Conditions
    for diagnosis in structured_data.diagnoses:
        condition = map_diagnosis_to_condition(diagnosis, patient_id)
        result["conditions"].append(condition.dict())

    # 3. Convert medications to MedicationRequests
    for medication in structured_data.medications:
        med_request = map_medication_to_request(medication, patient_id)
        result["medications"].append(med_request.dict())

    # 4. Convert vital signs to Observations
    if structured_data.vital_signs:
        vital_obs = map_vital_signs_to_observations(structured_data.vital_signs, patient_id)
        result["observations"].extend([obs.dict() for obs in vital_obs])

    # 5. Convert lab results to Observations (simplified text-only)
    for idx, lab_text in enumerate(structured_data.lab_results):
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
            "effectiveDateTime": datetime.now().isoformat(),
            "valueString": lab_text
        }
        result["observations"].append(Observation(**obs_data).dict())

    return result

print("✅ Main conversion function created")
```

**Estimated time:** 5 minutes

---

### 3.2 Test Full Conversion on SOAP Note Data (Notebook Cell)

**Add code cell:**

```python
# Convert the structured data we extracted earlier
print("=" * 80)
print("Converting structured data to FHIR resources...")
print("=" * 80)

fhir_resources = convert_to_fhir(structured_data, patient_id="patient-soap-01")

# Summary
print(f"\n✅ FHIR Conversion Complete!")
print(f"   • Patient: {1 if fhir_resources['patient'] else 0}")
print(f"   • Conditions: {len(fhir_resources['conditions'])}")
print(f"   • Medications: {len(fhir_resources['medications'])}")
print(f"   • Observations: {len(fhir_resources['observations'])}")

total_resources = (
    (1 if fhir_resources['patient'] else 0) +
    len(fhir_resources['conditions']) +
    len(fhir_resources['medications']) +
    len(fhir_resources['observations'])
)
print(f"   • Total resources: {total_resources}")
```

**Estimated time:** 3 minutes

---

### 3.3 Validate and Pretty Print Results (Notebook Cell)

**Add code cell to visualize FHIR resources:**

```python
# Pretty print each resource type
print("\n" + "=" * 80)
print("FHIR RESOURCES (Pretty Print)")
print("=" * 80)

if fhir_resources['patient']:
    print("\n🏥 PATIENT:")
    print(json.dumps(fhir_resources['patient'], indent=2))

if fhir_resources['conditions']:
    print(f"\n💊 CONDITIONS ({len(fhir_resources['conditions'])}):")
    for idx, condition in enumerate(fhir_resources['conditions'], 1):
        print(f"\nCondition {idx}:")
        print(json.dumps(condition, indent=2))

if fhir_resources['medications']:
    print(f"\n💉 MEDICATIONS ({len(fhir_resources['medications'])}):")
    for idx, med in enumerate(fhir_resources['medications'], 1):
        print(f"\nMedication {idx}:")
        print(json.dumps(med, indent=2))

if fhir_resources['observations']:
    print(f"\n📊 OBSERVATIONS ({len(fhir_resources['observations'])}):")
    for idx, obs in enumerate(fhir_resources['observations'][:3], 1):  # Show first 3
        print(f"\nObservation {idx}:")
        print(json.dumps(obs, indent=2))
    if len(fhir_resources['observations']) > 3:
        print(f"\n... and {len(fhir_resources['observations']) - 3} more observations")

print("\n" + "=" * 80)
print("✅ All FHIR resources validated successfully!")
print("=" * 80)
```

**Estimated time:** 4 minutes

---

### 3.4 Test on Multiple SOAP Notes (Notebook Cell - Optional)

**Add code cell to test with other SOAP notes:**

```python
# Test conversion on all SOAP notes we have results for
print("\n" + "=" * 80)
print("Testing FHIR conversion on multiple SOAP notes")
print("=" * 80)

fhir_results_all = {}

for soap_file, extracted_data in results.items():
    patient_id = f"patient-{soap_file.replace('.txt', '')}"
    fhir_result = convert_to_fhir(extracted_data, patient_id)
    fhir_results_all[soap_file] = fhir_result

    total = (
        (1 if fhir_result['patient'] else 0) +
        len(fhir_result['conditions']) +
        len(fhir_result['medications']) +
        len(fhir_result['observations'])
    )

    print(f"\n{soap_file}:")
    print(f"  • Total FHIR resources: {total}")
    print(f"    - Patient: {1 if fhir_result['patient'] else 0}")
    print(f"    - Conditions: {len(fhir_result['conditions'])}")
    print(f"    - Medications: {len(fhir_result['medications'])}")
    print(f"    - Observations: {len(fhir_result['observations'])}")

print("\n✅ FHIR conversion tested on all SOAP notes!")
```

**Estimated time:** 3 minutes

---

## Phase 4: Backend Service Integration (25 minutes)

### 4.1 Create FHIR Conversion Service Module

**File:** `backend/app/services/fhir_conversion.py`

**Copy working code from notebook and add service wrapper:**

```python
"""
FHIR R4 conversion service for structured clinical data.
"""

import logging
from typing import List, Optional
from datetime import datetime, date

from fhir.resources.patient import Patient
from fhir.resources.condition import Condition
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.observation import Observation
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.reference import Reference
from fhir.resources.identifier import Identifier
from fhir.resources.humanname import HumanName
from fhir.resources.quantity import Quantity

from app.schemas.extraction import (
    StructuredClinicalData,
    DiagnosisCode,
    MedicationCode,
    VitalSigns,
    PatientInfo,
)

logger = logging.getLogger(__name__)

class FHIRConversionService:
    """Service for converting structured clinical data to FHIR resources."""

    def convert_to_fhir(
        self,
        structured_data: StructuredClinicalData,
        patient_id: str = "unknown"
    ) -> dict:
        """
        Convert structured clinical data to FHIR R4 resources.

        Returns dict with:
        - patient: Patient resource
        - conditions: List of Condition resources
        - medications: List of MedicationRequest resources
        - observations: List of Observation resources (vitals + labs)
        """
        pass  # Implement main orchestration logic

    def map_patient_info_to_fhir(
        self,
        patient_info: Optional[PatientInfo],
        patient_id: str
    ) -> Optional[Patient]:
        """Map PatientInfo to FHIR Patient resource."""
        pass

    def map_diagnosis_to_condition(
        self,
        diagnosis: DiagnosisCode,
        patient_id: str
    ) -> Condition:
        """Map DiagnosisCode to FHIR Condition resource."""
        pass

    def map_medication_to_request(
        self,
        medication: MedicationCode,
        patient_id: str
    ) -> MedicationRequest:
        """Map MedicationCode to FHIR MedicationRequest resource."""
        pass

    def map_vital_signs_to_observations(
        self,
        vital_signs: Optional[VitalSigns],
        patient_id: str
    ) -> List[Observation]:
        """Map VitalSigns to FHIR Observation resources."""
        pass

    def map_lab_result_to_observation(
        self,
        lab_text: str,
        patient_id: str,
        index: int
    ) -> Observation:
        """Map lab result text to FHIR Observation resource."""
        pass


# Singleton pattern (similar to LLM service)
_fhir_service_instance: Optional[FHIRConversionService] = None

def get_fhir_service() -> FHIRConversionService:
    """Get or create singleton FHIR conversion service."""
    global _fhir_service_instance
    if _fhir_service_instance is None:
        _fhir_service_instance = FHIRConversionService()
        logger.info("FHIR conversion service initialized")
    return _fhir_service_instance
```

**Implementation approach:**

1. Copy all mapping functions from notebook
2. Add class wrapper and singleton pattern
3. Add logging and error handling
4. Import from existing schemas

**Key code structure:**

```python
"""
FHIR R4 conversion service for structured clinical data.
"""

import logging
from typing import List, Optional
from datetime import datetime

from fhir.resources.patient import Patient
from fhir.resources.condition import Condition
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.observation import Observation

from app.schemas.extraction import (
    StructuredClinicalData,
    DiagnosisCode,
    MedicationCode,
    VitalSigns,
    PatientInfo,
)

logger = logging.getLogger(__name__)


class FHIRConversionService:
    """Service for converting structured clinical data to FHIR resources."""

    # Copy all mapping functions from notebook:
    # - map_patient_info_to_fhir
    # - map_diagnosis_to_condition
    # - map_medication_to_request
    # - map_vital_signs_to_observations
    # - convert_to_fhir (main orchestration)


# Singleton pattern (similar to LLM/agent services)
_fhir_service_instance: Optional[FHIRConversionService] = None


def get_fhir_service() -> FHIRConversionService:
    """Get or create singleton FHIR conversion service."""
    global _fhir_service_instance
    if _fhir_service_instance is None:
        _fhir_service_instance = FHIRConversionService()
        logger.info("FHIR conversion service initialized")
    return _fhir_service_instance
```

**Steps:**

1. Create file with imports and class structure
2. Copy all 5 mapping functions from notebook (tested and working)
3. Convert standalone functions to class methods (add `self`)
4. Replace `print()` statements with `logger.warning()` or `logger.info()`
5. Add singleton getter function

**Estimated time:** 15 minutes

---

### 4.2 Create FHIR API Schemas

**File:** `backend/app/schemas/fhir.py`

**Purpose:** Request/response models for FHIR conversion endpoint

**Implementation:** Simple wrapper schemas around the FHIR resources

**Estimated time:** 10 minutes

---

## Phase 5: API Endpoint (15 minutes)

### 5.1 Create Request/Response Schemas

**File:** `backend/app/schemas/fhir.py`

**Implementation (simplified from notebook testing):**

```python
"""
Pydantic schemas for FHIR conversion API.
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

from app.schemas.extraction import StructuredClinicalData


class FHIRConversionRequest(BaseModel):
    """Request to convert structured data to FHIR."""
    structured_data: StructuredClinicalData = Field(
        ...,
        description="Structured clinical data from agent extraction"
    )
    patient_id: Optional[str] = Field(
        "unknown",
        description="Patient identifier (if known)"
    )


class FHIRConversionResponse(BaseModel):
    """Response containing FHIR resources."""
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
        description="FHIR Observation resources"
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
                        "code": {
                            "coding": [
                                {
                                    "system": "http://hl7.org/fhir/sid/icd-10-cm",
                                    "code": "E11.9",
                                    "display": "Type 2 diabetes mellitus without complications"
                                }
                            ],
                            "text": "Type 2 Diabetes Mellitus"
                        },
                        "clinicalStatus": {"coding": [{"code": "active"}]},
                        "subject": {"reference": "Patient/patient-123"}
                    }
                ],
                "medications": [],
                "observations": [],
                "resource_count": 5,
                "processing_time_ms": 145
            }
        }
```

**Estimated time:** 5 minutes

---

### 5.2 Create FHIR Router

**File:** `backend/app/api/routes/fhir.py`

**Implementation:**

```python
"""
FHIR conversion API routes.
"""

import logging
import time
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status

from app.schemas.fhir import FHIRConversionRequest, FHIRConversionResponse
from app.services.fhir_conversion import get_fhir_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/convert", response_model=FHIRConversionResponse)
async def convert_to_fhir(request: FHIRConversionRequest) -> FHIRConversionResponse:
    """
    Convert structured clinical data to FHIR R4 resources.

    Takes the output from the agent extraction endpoint (Part 4) and converts
    it to FHIR-compliant JSON resources including Patient, Condition,
    MedicationRequest, and Observation.

    **Mappings:**
    - patient_info → Patient
    - diagnoses (with ICD-10-CM) → Condition
    - medications (with RxNorm) → MedicationRequest
    - vital_signs → Observation (vital-signs category)
    - lab_results → Observation (laboratory category)
    """
    start_time = time.time()

    try:
        logger.info(f"FHIR conversion request for patient: {request.patient_id}")

        # Get FHIR service
        fhir_service = get_fhir_service()

        # Convert to FHIR
        fhir_resources = fhir_service.convert_to_fhir(
            structured_data=request.structured_data,
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


@router.get("/health")
async def fhir_health_check() -> Dict[str, Any]:
    """Health check for FHIR conversion service."""
    try:
        fhir_service = get_fhir_service()
        return {
            "status": "ok",
            "service": "FHIR Conversion",
            "fhir_version": "R4"
        }
    except Exception as e:
        logger.error(f"FHIR health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="FHIR service unavailable"
        )
```

**Estimated time:** 6 minutes

---

### 5.3 Register Router in Main App

**File:** `backend/app/main.py`

**Changes:**

```python
# Add import
from app.api.routes import fhir

# Register router (add with other routers)
app.include_router(
    fhir.router,
    prefix="/fhir",
    tags=["FHIR Conversion"]
)
```

**Test in Swagger UI:**

- Navigate to `http://localhost:8000/docs`
- Find `/fhir/convert` endpoint
- Test with sample structured data

**Estimated time:** 4 minutes

---

## Phase 6: Testing & Documentation (20 minutes)

### 6.1 Create Integration Test Script

**File:** `backend/tests/test_fhir_conversion.py`

**Purpose:** End-to-end test combining agent extraction + FHIR conversion

**Implementation:**

```python
"""
Integration test for FHIR conversion endpoint.

Tests the full pipeline: SOAP note → Agent extraction → FHIR conversion
"""

import httpx
import json
from pathlib import Path


def test_full_pipeline_soap_01():
    """Test extraction + FHIR conversion for SOAP note 01."""

    base_url = "http://localhost:8000"

    # 1. Load SOAP note
    soap_path = Path(__file__).parent.parent.parent / "med_docs" / "soap" / "soap_01.txt"
    with open(soap_path) as f:
        soap_text = f.read()

    print("=" * 80)
    print("STEP 1: Extract structured data from SOAP note")
    print("=" * 80)

    # 2. Call agent extraction endpoint
    extraction_response = httpx.post(
        f"{base_url}/agent/extract_structured",
        json={"text": soap_text},
        timeout=60.0
    )

    assert extraction_response.status_code == 200
    structured_data = extraction_response.json()

    print(f"Extracted {len(structured_data['diagnoses'])} diagnoses")
    print(f"Extracted {len(structured_data['medications'])} medications")
    print()

    # 3. Call FHIR conversion endpoint
    print("=" * 80)
    print("STEP 2: Convert to FHIR resources")
    print("=" * 80)

    fhir_response = httpx.post(
        f"{base_url}/fhir/convert",
        json={
            "structured_data": structured_data,
            "patient_id": "patient-soap-01"
        },
        timeout=30.0
    )

    assert fhir_response.status_code == 200
    fhir_resources = fhir_response.json()

    # 4. Validate FHIR resources
    print(f"Created {fhir_resources['resource_count']} FHIR resources:")
    print(f"  - Patient: {1 if fhir_resources['patient'] else 0}")
    print(f"  - Conditions: {len(fhir_resources['conditions'])}")
    print(f"  - Medications: {len(fhir_resources['medications'])}")
    print(f"  - Observations: {len(fhir_resources['observations'])}")
    print()

    # 5. Validate structure
    if fhir_resources["patient"]:
        assert fhir_resources["patient"]["resourceType"] == "Patient"

    for condition in fhir_resources["conditions"]:
        assert condition["resourceType"] == "Condition"
        assert "code" in condition
        assert "subject" in condition

    for med in fhir_resources["medications"]:
        assert med["resourceType"] == "MedicationRequest"
        assert "medicationCodeableConcept" in med

    for obs in fhir_resources["observations"]:
        assert obs["resourceType"] == "Observation"
        assert "code" in obs

    print("✅ All FHIR resources validated successfully!")
    print()

    # 6. Pretty print first Condition
    if fhir_resources["conditions"]:
        print("=" * 80)
        print("EXAMPLE: First Condition Resource")
        print("=" * 80)
        print(json.dumps(fhir_resources["conditions"][0], indent=2))

    return fhir_resources


if __name__ == "__main__":
    test_full_pipeline_soap_01()
```

**Run test:**

```bash
poetry run python backend/tests/test_fhir_conversion.py
```

**Estimated time:** 10 minutes

---

### 6.2 Update README Documentation

**File:** `backend/README.md`

**Add section:**

````markdown
#### FHIR Conversion

```http
POST /fhir/convert
Content-Type: application/json

{
  "structured_data": {
    "patient_info": {"age": "45", "gender": "male"},
    "diagnoses": [
      {
        "text": "Type 2 Diabetes Mellitus",
        "icd10_code": "E11.9",
        "icd10_description": "Type 2 diabetes mellitus without complications",
        "confidence": "exact"
      }
    ],
    "medications": [...],
    "vital_signs": {...},
    "lab_results": [...],
    "plan_actions": [...]
  },
  "patient_id": "patient-123"
}
```
````

Convert structured clinical data (from agent extraction) to FHIR R4 resources.

**Features:**

- Converts to FHIR R4-compliant resources
- Uses official `fhir.resources` Python library
- Maps ICD-10-CM codes to Condition resources
- Maps RxNorm codes to MedicationRequest resources
- Converts vitals and labs to Observation resources
- Creates Patient resource from demographics

**Response:**

```json
{
  "patient": {
    "resourceType": "Patient",
    "id": "patient-123",
    "gender": "male",
    "birthDate": "1978-01-01"
  },
  "conditions": [
    {
      "resourceType": "Condition",
      "clinicalStatus": {...},
      "verificationStatus": {...},
      "code": {
        "coding": [
          {
            "system": "http://hl7.org/fhir/sid/icd-10-cm",
            "code": "E11.9",
            "display": "Type 2 diabetes mellitus without complications"
          }
        ],
        "text": "Type 2 Diabetes Mellitus"
      },
      "subject": {"reference": "Patient/patient-123"},
      "recordedDate": "2025-11-29T12:34:56"
    }
  ],
  "medications": [...],
  "observations": [...],
  "resource_count": 8,
  "processing_time_ms": 145
}
```

**FHIR Resource Mappings:**

| Source Data  | FHIR Resource     | Coding System |
| ------------ | ----------------- | ------------- |
| patient_info | Patient           | N/A           |
| diagnoses    | Condition         | ICD-10-CM     |
| medications  | MedicationRequest | RxNorm        |
| vital_signs  | Observation       | LOINC         |
| lab_results  | Observation       | Text-only     |

**Health Check:**

```http
GET /fhir/health
```

**Testing:**

```bash
# Integration test (extraction + FHIR conversion)
poetry run python tests/test_fhir_conversion.py
```

````

**Update Project Status section:**

```markdown
**Part 5: FHIR Conversion**

- [x] fhir.resources library integration
- [x] FHIR R4 conversion service
- [x] Patient resource mapping
- [x] Condition resource mapping (ICD-10-CM codes)
- [x] MedicationRequest resource mapping (RxNorm codes)
- [x] Observation resource mapping (vitals + labs with LOINC)
- [x] FHIR conversion endpoint (`POST /fhir/convert`)
- [x] FHIR health check endpoint
- [x] Integration test script
- [x] Documentation with examples
````

**Estimated time:** 8 minutes

---

### 6.3 Add Inline Documentation

**Add docstrings to all functions:**

- Explain what each mapping function does
- Document FHIR resource structure
- Add examples in docstrings
- Explain simplifications made

**Estimated time:** 2 minutes

---

## Implementation Order

**Recommended sequence (Notebook → Backend):**

1. **Setup** (10 min)

   - Install `fhir.resources`
   - Add notebook section
   - Test imports in notebook

2. **Notebook Prototyping** (45 min)

   - Implement all FHIR mapping functions in notebook
   - Test each function independently
   - Create main conversion orchestrator
   - Test on multiple SOAP notes
   - Validate all FHIR resources
   - Iterate until working perfectly

3. **Backend Integration** (25 min)

   - Copy working code to service module
   - Convert to class methods
   - Add logging and error handling
   - Create API schemas

4. **API Endpoint** (15 min)

   - Build FHIR router
   - Register router
   - Test via Swagger UI

5. **Testing & Docs** (20 min)
   - Create integration test
   - Update README
   - Add docstrings

---

## Success Criteria

- [x] `fhir.resources` library installed and working
- [x] FHIR conversion service with all mapping functions
- [x] `POST /fhir/convert` endpoint working
- [x] Patient resource created from patient_info
- [x] Condition resources created with ICD-10-CM codes
- [x] MedicationRequest resources created with RxNorm codes
- [x] Observation resources created for vitals (with LOINC)
- [x] Observation resources created for labs
- [x] All FHIR resources validate against R4 spec (via fhir.resources)
- [x] Integration test passes (extraction → FHIR)
- [x] Documentation updated with examples

---

## Time Allocation Summary

| Phase                               | Time        |
| ----------------------------------- | ----------- |
| Phase 1: Setup & Dependencies       | 10 min      |
| Phase 2: FHIR Mapping (Notebook)    | 30 min      |
| Phase 3: Test Conversion (Notebook) | 15 min      |
| Phase 4: Backend Service            | 25 min      |
| Phase 5: API Endpoint               | 15 min      |
| Phase 6: Testing & Documentation    | 20 min      |
| Buffer                              | 5 min       |
| **Total**                           | **2 hours** |

---

## Key Design Decisions

### Why Use `fhir.resources` Library?

- ✅ Official FHIR R4 Python implementation
- ✅ Pydantic-based (familiar from project)
- ✅ Automatic validation against FHIR spec
- ✅ Handles all resource types
- ✅ Easy serialization to/from JSON
- ✅ Well-maintained and documented

### Simplifications Made

1. **Patient birthDate**: Derived from age (approximate)
2. **Condition status**: All set to "active" + "confirmed"
3. **Observation values**: Using `valueString` for simplicity (not parsing units)
4. **Lab results**: Text-only codes (no standardized coding without more context)
5. **MedicationRequest dosage**: Not parsing dosage instructions (could be added)
6. **Encounter context**: Not creating Encounter resources (out of scope)

### What We're NOT Doing (Out of Scope)

- ❌ Full FHIR validation server
- ❌ FHIR Bundle creation (could be stretch goal)
- ❌ FHIR persistence/storage
- ❌ FHIR search parameters
- ❌ Parsing dosage instructions into structured format
- ❌ Creating Practitioner/Organization resources
- ❌ Handling multiple patient records
- ❌ FHIR extensions

### FHIR Spec Compliance

**What we comply with:**

- ✅ FHIR R4 resource structure
- ✅ Required fields for each resource type
- ✅ Standard coding systems (ICD-10-CM, RxNorm, LOINC)
- ✅ Proper CodeableConcept structure
- ✅ Patient references in all clinical resources

**Simplifications:**

- Uses approximate dates where exact dates unavailable
- Generic "unknown" patient ID if not provided
- Minimal metadata (no Practitioner, Organization)
- Text-only codes for lab results

---

## Potential Challenges & Mitigations

| Challenge                              | Mitigation                                     |
| -------------------------------------- | ---------------------------------------------- |
| `fhir.resources` has complex structure | Use Pydantic dict() method, test incrementally |
| Missing patient demographics           | Use placeholder values, make optional          |
| Vital signs need proper units          | Use valueString for simplicity                 |
| Lab results have no standardized codes | Use text-only codes, document limitation       |
| LOINC codes may be unfamiliar          | Use standard LOINC codes for common vitals     |
| Testing requires real agent output     | Create integration test with real SOAP notes   |

---

## FHIR Resource Templates

### Patient Example

```json
{
  "resourceType": "Patient",
  "id": "patient-123",
  "identifier": [
    {
      "system": "urn:oid:df-healthbench",
      "value": "patient-123"
    }
  ],
  "gender": "male",
  "birthDate": "1978-01-01"
}
```

---

### Condition Example

```json
{
  "resourceType": "Condition",
  "clinicalStatus": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
        "code": "active"
      }
    ]
  },
  "verificationStatus": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        "code": "confirmed"
      }
    ]
  },
  "code": {
    "coding": [
      {
        "system": "http://hl7.org/fhir/sid/icd-10-cm",
        "code": "E11.9",
        "display": "Type 2 diabetes mellitus without complications"
      }
    ],
    "text": "Type 2 Diabetes Mellitus"
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "recordedDate": "2025-11-29T12:34:56"
}
```

---

### MedicationRequest Example

```json
{
  "resourceType": "MedicationRequest",
  "status": "active",
  "intent": "order",
  "medicationCodeableConcept": {
    "coding": [
      {
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "860975",
        "display": "Metformin 500 MG Oral Tablet"
      }
    ],
    "text": "Metformin 500mg twice daily"
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "authoredOn": "2025-11-29T12:34:56"
}
```

---

### Observation Example (Vital Sign)

```json
{
  "resourceType": "Observation",
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "vital-signs"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "8867-4",
        "display": "Heart rate"
      }
    ],
    "text": "Heart rate"
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "effectiveDateTime": "2025-11-29T12:34:56",
  "valueString": "72 bpm"
}
```

---

## LOINC Codes Reference

Common vital signs with LOINC codes:

| Vital Sign        | LOINC Code | Display Name         |
| ----------------- | ---------- | -------------------- |
| Blood Pressure    | 85354-9    | Blood pressure panel |
| Heart Rate        | 8867-4     | Heart rate           |
| Respiratory Rate  | 9279-1     | Respiratory rate     |
| Body Temperature  | 8310-5     | Body temperature     |
| Oxygen Saturation | 2708-6     | Oxygen saturation    |
| Body Weight       | 29463-7    | Body weight          |
| Body Height       | 8302-2     | Body height          |
| BMI               | 39156-5    | Body mass index      |

---

## Testing Strategy

### Manual Testing

1. Start backend server
2. Test extraction endpoint with SOAP note → get structured data
3. Test FHIR conversion endpoint with structured data
4. Validate FHIR resources in response
5. Check resource structure in Swagger UI

### Integration Testing

1. Create `test_fhir_conversion.py`
2. Test full pipeline: SOAP note → extraction → FHIR
3. Validate all resource types created
4. Check ICD-10-CM codes in Conditions
5. Check RxNorm codes in MedicationRequests
6. Check LOINC codes in Observations
7. Verify resource references are correct

### Validation

1. Use `fhir.resources` library validation (automatic)
2. Check resourceType on all resources
3. Verify required fields present
4. Test with multiple SOAP notes

---

## Stretch Goals (If Time Permits)

- [ ] Create FHIR Bundle resource wrapping all resources
- [ ] Add proper Quantity parsing for vital signs (with units)
- [ ] Parse medication dosage instructions into structured format
- [ ] Add FHIR validation endpoint (validate any FHIR JSON)
- [ ] Support FHIR search parameters (e.g., get by patient ID)
- [ ] Add CarePlan resource for plan_actions
- [ ] Create Encounter resource for visit context
- [ ] Add support for multiple patients in one request
- [ ] Generate FHIR narrative text (human-readable HTML)
- [ ] Add FHIR extensions for custom fields

---

## Notes & Reminders

- **Notebook first, backend second**: Develop and test in notebook, then copy to backend (same as Sprint 4)
- **Use fhir.resources dict()**: Convert resources to dict for JSON response
- **Handle missing data gracefully**: Not all notes have complete info
- **Reference patient ID consistently**: Use "Patient/{patient_id}" format
- **Use standard coding systems**: ICD-10-CM, RxNorm, LOINC
- **Log conversion steps**: Helps debug mapping issues
- **Keep it simple**: Focus on core resources (Patient, Condition, Medication, Observation)
- **Test incrementally**: Test each mapping function separately in notebook before combining
- **Reuse agent extraction results**: No need to re-run agent, use existing `structured_data` variable
- **Don't over-engineer**: Simplified FHIR is acceptable for this project

---

## Next Steps (Post-Sprint)

After completing Part 5, the project will be ready for:

**Part 6: Containerization**

- Create Dockerfile for backend
- Complete docker-compose.yml with all services
- Add environment variable management
- Create startup scripts
- Production-ready deployment
- Final README with deployment instructions

---

## References

- **FHIR R4 Spec**: https://hl7.org/fhir/R4/
- **fhir.resources Library**: https://pypi.org/project/fhir.resources/
- **LOINC Database**: https://loinc.org/
- **ICD-10-CM**: https://www.cms.gov/medicare/coordination-benefits-recovery/overview/icd-code-lists
- **RxNorm**: https://www.nlm.nih.gov/research/umls/rxnorm/

---

## Appendix: Common FHIR Gotchas

1. **CodeableConcept vs Code**: Use CodeableConcept for clinical codes (contains Coding + text)
2. **Status fields are required**: All resources need status (active, final, etc.)
3. **References use format**: "ResourceType/id" not just "id"
4. **Dates vs DateTimes**: Use appropriate type (birthDate vs effectiveDateTime)
5. **Pydantic dict() method**: Use `resource.dict()` to serialize to JSON
6. **fhir.resources validation**: Will raise errors if required fields missing

---

## Implementation Checklist

**Phase 1: Setup (Notebook)**

- [ ] Install fhir.resources library
- [ ] Add Section 6 to notebook
- [ ] Test FHIR imports in notebook
- [ ] Verify access to structured_data from agent

**Phase 2: FHIR Mapping (Notebook)**

- [ ] Add mapping strategy markdown
- [ ] Implement map_patient_info_to_fhir in notebook
- [ ] Implement map_diagnosis_to_condition in notebook
- [ ] Implement map_medication_to_request in notebook
- [ ] Implement map_vital_signs_to_observations in notebook
- [ ] Test each function independently

**Phase 3: Test Conversion (Notebook)**

- [ ] Create convert_to_fhir orchestration function
- [ ] Test full conversion on SOAP data
- [ ] Pretty print and validate FHIR resources
- [ ] Test on multiple SOAP notes

**Phase 4: Backend Service**

- [ ] Create services/fhir_conversion.py
- [ ] Copy all mapping functions from notebook
- [ ] Convert to class methods
- [ ] Add logging and error handling
- [ ] Create API schemas (schemas/fhir.py)

**Phase 5: API Endpoint**

- [ ] Create api/routes/fhir.py
- [ ] Implement POST /fhir/convert endpoint
- [ ] Implement GET /fhir/health endpoint
- [ ] Register router in main.py
- [ ] Test in Swagger UI

**Phase 6: Testing & Docs**

- [ ] Create tests/test_fhir_conversion.py
- [ ] Run integration test
- [ ] Update README.md with FHIR section
- [ ] Add docstrings to all functions
- [ ] Update project status

---

**Ready to begin! 🚀**
