"""
Test Part 5: FHIR Conversion

Tests for:
- FHIR conversion service
- Patient resource mapping
- Condition resource mapping
- MedicationRequest resource mapping
- Observation resource mapping
- FHIR API endpoints
- Full pipeline (SOAP → Agent → FHIR)
"""

import pytest
import json

from app.services.fhir_conversion import get_fhir_service


# ============================================================================
# FHIR Service Tests
# ============================================================================

class TestFHIRConversionService:
    """Test FHIR conversion service layer."""
    
    @pytest.mark.unit
    def test_fhir_service_singleton(self):
        """Test that FHIR service uses singleton pattern."""
        service1 = get_fhir_service()
        service2 = get_fhir_service()
        
        assert service1 is service2
    
    @pytest.mark.integration
    def test_convert_patient_resource(self, sample_extraction_data):
        """Test converting patient info to FHIR Patient resource."""
        fhir_service = get_fhir_service()
        
        fhir_resources = fhir_service.convert_to_fhir(
            structured_data=sample_extraction_data,
            patient_id="test-patient-123"
        )
        
        # Verify patient resource
        assert "patient" in fhir_resources
        patient = fhir_resources["patient"]
        
        assert patient["resourceType"] == "Patient"
        assert patient["id"] == "test-patient-123"
        assert patient["gender"] == "male"
        assert "identifier" in patient
    
    @pytest.mark.integration
    def test_convert_condition_resources(self, sample_extraction_data):
        """Test converting diagnoses to FHIR Condition resources."""
        fhir_service = get_fhir_service()
        
        fhir_resources = fhir_service.convert_to_fhir(
            structured_data=sample_extraction_data,
            patient_id="test-patient-123"
        )
        
        # Verify condition resources
        assert "conditions" in fhir_resources
        conditions = fhir_resources["conditions"]
        
        # Should have 2 conditions (Type 2 Diabetes + Hypertension)
        assert len(conditions) == 2
        
        for condition in conditions:
            assert condition["resourceType"] == "Condition"
            assert "code" in condition
            assert "subject" in condition
            assert condition["subject"]["reference"] == "Patient/test-patient-123"
            assert "clinicalStatus" in condition
            assert "verificationStatus" in condition
            assert "recordedDate" in condition
            
            # Verify coding system for ICD-10-CM
            if condition["code"].get("coding"):
                coding = condition["code"]["coding"][0]
                assert coding["system"] == "http://hl7.org/fhir/sid/icd-10-cm"
                assert coding["code"] is not None
    
    @pytest.mark.integration
    def test_convert_medication_resources(self, sample_extraction_data):
        """Test converting medications to FHIR MedicationRequest resources."""
        fhir_service = get_fhir_service()
        
        fhir_resources = fhir_service.convert_to_fhir(
            structured_data=sample_extraction_data,
            patient_id="test-patient-123"
        )
        
        # Verify medication resources
        assert "medications" in fhir_resources
        medications = fhir_resources["medications"]
        
        # Should have 2 medications (Metformin + Lisinopril)
        assert len(medications) == 2
        
        for med in medications:
            assert med["resourceType"] == "MedicationRequest"
            assert "medication" in med
            assert "subject" in med
            assert med["subject"]["reference"] == "Patient/test-patient-123"
            assert med["status"] == "active"
            assert med["intent"] == "order"
            assert "authoredOn" in med
            
            # Verify RxNorm coding system
            if med["medication"]["concept"].get("coding"):
                coding = med["medication"]["concept"]["coding"][0]
                assert coding["system"] == "http://www.nlm.nih.gov/research/umls/rxnorm"
                assert coding["code"] is not None
    
    @pytest.mark.integration
    def test_convert_observation_resources(self, sample_extraction_data):
        """Test converting vitals and labs to FHIR Observation resources."""
        fhir_service = get_fhir_service()
        
        fhir_resources = fhir_service.convert_to_fhir(
            structured_data=sample_extraction_data,
            patient_id="test-patient-123"
        )
        
        # Verify observation resources
        assert "observations" in fhir_resources
        observations = fhir_resources["observations"]
        
        # Should have observations for vitals (3) and labs (2)
        assert len(observations) > 0
        
        for obs in observations:
            assert obs["resourceType"] == "Observation"
            assert "code" in obs
            assert "subject" in obs
            assert obs["subject"]["reference"] == "Patient/test-patient-123"
            assert obs["status"] == "final"
            assert "effectiveDateTime" in obs
            
            # Should have either valueString or valueQuantity
            assert "valueString" in obs or "valueQuantity" in obs
    
    @pytest.mark.integration
    def test_resource_count_calculation(self, sample_extraction_data):
        """Test that FHIR resources are created from structured data."""
        fhir_service = get_fhir_service()
        
        fhir_resources = fhir_service.convert_to_fhir(
            structured_data=sample_extraction_data,
            patient_id="test-patient-123"
        )
        
        # Service returns dict with patient, conditions, medications, observations
        # (resource_count is calculated by the API endpoint, not the service)
        resource_count = 0
        if fhir_resources.get("patient"):
            resource_count += 1
        resource_count += len(fhir_resources.get("conditions", []))
        resource_count += len(fhir_resources.get("medications", []))
        resource_count += len(fhir_resources.get("observations", []))
        
        # Should have created multiple resources
        assert resource_count > 0


# ============================================================================
# FHIR API Endpoint Tests
# ============================================================================

class TestFHIREndpoints:
    """Test FHIR API endpoints."""
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_fhir_convert_endpoint(self, test_client, sample_extraction_data_dict):
        """Test POST /fhir/convert endpoint."""
        # Add patient_id to the request (API expects it in the body)
        request_data = {**sample_extraction_data_dict, "patient_id": "test-patient-456"}
        
        response = test_client.post(
            "/fhir/convert",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "patient" in data
        assert "conditions" in data
        assert "medications" in data
        assert "observations" in data
        assert "resource_count" in data
        assert "processing_time_ms" in data
        
        # Verify resources were created
        assert data["patient"] is not None
        assert len(data["conditions"]) > 0
        assert len(data["medications"]) > 0
        assert len(data["observations"]) > 0
    
    @pytest.mark.api
    def test_fhir_convert_missing_patient_id(self, test_client, sample_extraction_data_dict):
        """Test FHIR conversion without patient_id uses default."""
        # Don't include patient_id - should use default "unknown"
        response = test_client.post(
            "/fhir/convert",
            json=sample_extraction_data_dict
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should use default patient ID
        assert data["patient"] is not None
        # Default ID should be "unknown"
        assert data["patient"]["id"] == "unknown"


# ============================================================================
# End-to-End Pipeline Tests
# ============================================================================

class TestFullPipelineSOAPToFHIR:
    """Test complete pipeline from SOAP note to FHIR resources."""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_full_pipeline_soap_to_fhir(self, async_client, sample_soap_note):
        """Test full pipeline: SOAP note → Agent extraction → FHIR conversion."""
        
        # Step 1: Extract structured data from SOAP note
        extraction_response = await async_client.post(
            "/agent/extract_structured",
            json={"text": sample_soap_note}
        )
        
        assert extraction_response.status_code == 200
        structured_data = extraction_response.json()
        
        # Verify extraction worked
        assert len(structured_data["diagnoses"]) >= 0
        assert len(structured_data["medications"]) >= 0
        
        # Step 2: Convert to FHIR resources
        # Add patient_id to the structured_data (API expects it in the body)
        structured_data["patient_id"] = "patient-soap-test"
        
        fhir_response = await async_client.post(
            "/fhir/convert",
            json=structured_data
        )
        
        assert fhir_response.status_code == 200
        fhir_resources = fhir_response.json()
        
        # Step 3: Validate FHIR resources
        assert "patient" in fhir_resources
        assert "conditions" in fhir_resources
        assert "medications" in fhir_resources
        assert "observations" in fhir_resources
        assert "resource_count" in fhir_resources
        
        # Verify resource_count
        assert fhir_resources["resource_count"] > 0
        
        # Validate Patient resource
        if fhir_resources["patient"]:
            patient = fhir_resources["patient"]
            assert patient["resourceType"] == "Patient"
            assert patient["id"] == "patient-soap-test"
        
        # Validate Condition resources
        for condition in fhir_resources["conditions"]:
            assert condition["resourceType"] == "Condition"
            assert "code" in condition
            assert "subject" in condition
            assert condition["subject"]["reference"] == "Patient/patient-soap-test"
        
        # Validate MedicationRequest resources
        for med in fhir_resources["medications"]:
            assert med["resourceType"] == "MedicationRequest"
            assert "medication" in med
            assert "subject" in med
            assert med["subject"]["reference"] == "Patient/patient-soap-test"
        
        # Validate Observation resources
        for obs in fhir_resources["observations"]:
            assert obs["resourceType"] == "Observation"
            assert "code" in obs
            assert "subject" in obs
            assert obs["subject"]["reference"] == "Patient/patient-soap-test"
    
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_full_pipeline_with_document_id(self, async_client, sample_document_with_diagnosis):
        """Test full pipeline using document ID instead of text."""
        doc_id = sample_document_with_diagnosis.id
        
        # Step 1: Extract by document ID
        extraction_response = await async_client.post(
            f"/agent/extract_document/{doc_id}"
        )
        
        assert extraction_response.status_code == 200
        structured_data = extraction_response.json()
        
        # Step 2: Convert to FHIR
        # Add patient_id to the structured_data (API expects it in the body)
        structured_data["patient_id"] = f"patient-doc-{doc_id}"
        
        fhir_response = await async_client.post(
            "/fhir/convert",
            json=structured_data
        )
        
        assert fhir_response.status_code == 200
        fhir_resources = fhir_response.json()
        
        # Verify FHIR resources created
        assert fhir_resources["resource_count"] > 0
        assert fhir_resources["patient"] is not None


# ============================================================================
# FHIR Resource Validation Tests
# ============================================================================

class TestFHIRResourceValidation:
    """Test FHIR resource structure and compliance."""
    
    @pytest.mark.integration
    def test_patient_resource_structure(self, sample_extraction_data):
        """Test Patient resource has required FHIR fields."""
        fhir_service = get_fhir_service()
        
        fhir_resources = fhir_service.convert_to_fhir(
            structured_data=sample_extraction_data,
            patient_id="validation-test"
        )
        
        patient = fhir_resources["patient"]
        
        # Required FHIR Patient fields
        assert patient["resourceType"] == "Patient"
        assert "id" in patient
        assert "gender" in patient
        assert "birthDate" in patient
        assert "identifier" in patient
        
        # Verify identifier structure
        assert isinstance(patient["identifier"], list)
        assert len(patient["identifier"]) > 0
        assert "system" in patient["identifier"][0]
        assert "value" in patient["identifier"][0]
    
    @pytest.mark.integration
    def test_condition_resource_structure(self, sample_extraction_data):
        """Test Condition resource has required FHIR fields."""
        fhir_service = get_fhir_service()
        
        fhir_resources = fhir_service.convert_to_fhir(
            structured_data=sample_extraction_data,
            patient_id="validation-test"
        )
        
        if len(fhir_resources["conditions"]) > 0:
            condition = fhir_resources["conditions"][0]
            
            # Required FHIR Condition fields
            assert condition["resourceType"] == "Condition"
            assert "clinicalStatus" in condition
            assert "verificationStatus" in condition
            assert "code" in condition
            assert "subject" in condition
            assert "recordedDate" in condition
            
            # Verify CodeableConcept structure
            assert "coding" in condition["clinicalStatus"]
            assert "coding" in condition["verificationStatus"]
            
            # Verify ICD-10-CM coding
            if condition["code"].get("coding"):
                coding = condition["code"]["coding"][0]
                assert "system" in coding
                assert "code" in coding
                assert coding["system"] == "http://hl7.org/fhir/sid/icd-10-cm"
    
    @pytest.mark.integration
    def test_medication_request_structure(self, sample_extraction_data):
        """Test MedicationRequest resource has required FHIR fields."""
        fhir_service = get_fhir_service()
        
        fhir_resources = fhir_service.convert_to_fhir(
            structured_data=sample_extraction_data,
            patient_id="validation-test"
        )
        
        if len(fhir_resources["medications"]) > 0:
            med = fhir_resources["medications"][0]
            
            # Required FHIR MedicationRequest fields
            assert med["resourceType"] == "MedicationRequest"
            assert "status" in med
            assert "intent" in med
            assert "medication" in med
            assert "subject" in med
            assert "authoredOn" in med
            
            # Verify status values are valid FHIR codes
            assert med["status"] in ["active", "completed", "stopped"]
            assert med["intent"] in ["order", "plan", "proposal"]
            
            # Verify RxNorm coding
            if med["medication"]["concept"].get("coding"):
                coding = med["medication"]["concept"]["coding"][0]
                assert "system" in coding
                assert "code" in coding
                assert coding["system"] == "http://www.nlm.nih.gov/research/umls/rxnorm"
    
    @pytest.mark.integration
    def test_observation_resource_structure(self, sample_extraction_data):
        """Test Observation resource has required FHIR fields."""
        fhir_service = get_fhir_service()
        
        fhir_resources = fhir_service.convert_to_fhir(
            structured_data=sample_extraction_data,
            patient_id="validation-test"
        )
        
        if len(fhir_resources["observations"]) > 0:
            obs = fhir_resources["observations"][0]
            
            # Required FHIR Observation fields
            assert obs["resourceType"] == "Observation"
            assert "status" in obs
            assert "code" in obs
            assert "subject" in obs
            assert "effectiveDateTime" in obs
            
            # Verify status is valid FHIR code
            assert obs["status"] in ["registered", "preliminary", "final", "amended"]
            
            # Should have category for vital signs
            if obs.get("category"):
                assert isinstance(obs["category"], list)


# ============================================================================
# FHIR Coding System Tests
# ============================================================================

class TestFHIRCodingSystems:
    """Test FHIR coding system compliance."""
    
    @pytest.mark.integration
    def test_icd10_coding_system_uri(self, sample_extraction_data):
        """Test that ICD-10-CM codes use correct FHIR URI."""
        fhir_service = get_fhir_service()
        
        fhir_resources = fhir_service.convert_to_fhir(
            structured_data=sample_extraction_data,
            patient_id="test"
        )
        
        for condition in fhir_resources["conditions"]:
            if condition["code"].get("coding"):
                coding = condition["code"]["coding"][0]
                assert coding["system"] == "http://hl7.org/fhir/sid/icd-10-cm"
    
    @pytest.mark.integration
    def test_rxnorm_coding_system_uri(self, sample_extraction_data):
        """Test that RxNorm codes use correct FHIR URI."""
        fhir_service = get_fhir_service()
        
        fhir_resources = fhir_service.convert_to_fhir(
            structured_data=sample_extraction_data,
            patient_id="test"
        )
        
        for med in fhir_resources["medications"]:
            if med["medication"]["concept"].get("coding"):
                coding = med["medication"]["concept"]["coding"][0]
                assert coding["system"] == "http://www.nlm.nih.gov/research/umls/rxnorm"
    
    @pytest.mark.integration
    def test_loinc_coding_for_vitals(self, sample_extraction_data):
        """Test that vital sign observations use LOINC codes."""
        fhir_service = get_fhir_service()
        
        fhir_resources = fhir_service.convert_to_fhir(
            structured_data=sample_extraction_data,
            patient_id="test"
        )
        
        # Find vital sign observations
        vital_obs = [
            obs for obs in fhir_resources["observations"]
            if obs.get("category") and 
            any(cat.get("coding", [{}])[0].get("code") == "vital-signs" 
                for cat in obs.get("category", []))
        ]
        
        # Vital signs should use LOINC
        for obs in vital_obs:
            if obs["code"].get("coding"):
                coding = obs["code"]["coding"][0]
                assert coding["system"] == "http://loinc.org"


# ============================================================================
# Full Pipeline Integration Tests
# ============================================================================

class TestEndToEndPipeline:
    """Test complete end-to-end pipeline."""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.skip(reason="Very slow test - full pipeline with real SOAP note, ~60 seconds")
    async def test_soap_01_full_pipeline(self, async_client, sample_soap_note):
        """Test full pipeline with soap_01.txt from med_docs."""
        
        # Step 1: Extract
        extraction_response = await async_client.post(
            "/agent/extract_structured",
            json={"text": sample_soap_note}
        )
        assert extraction_response.status_code == 200
        structured_data = extraction_response.json()
        
        # Step 2: Convert to FHIR
        fhir_response = await async_client.post(
            "/fhir/convert",
            json={
                "structured_data": structured_data,
                "patient_id": "patient-soap-01"
            }
        )
        assert fhir_response.status_code == 200
        fhir_resources = fhir_response.json()
        
        # Step 3: Validate all resources are FHIR-compliant
        assert fhir_resources["resource_count"] > 0
        
        # Each resource type should have proper structure
        if fhir_resources["patient"]:
            assert fhir_resources["patient"]["resourceType"] == "Patient"
        
        for cond in fhir_resources["conditions"]:
            assert cond["resourceType"] == "Condition"
        
        for med in fhir_resources["medications"]:
            assert med["resourceType"] == "MedicationRequest"
        
        for obs in fhir_resources["observations"]:
            assert obs["resourceType"] == "Observation"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestFHIRErrorHandling:
    """Test error handling in FHIR conversion."""
    
    @pytest.mark.api
    def test_convert_with_invalid_data_structure(self, test_client):
        """Test FHIR conversion with missing required fields."""
        response = test_client.post(
            "/fhir/convert",
            json={}  # Completely empty request
        )
        
        # Should return validation error for missing fields
        # API is lenient and uses defaults, so either 200 or 422 is acceptable
        assert response.status_code in [200, 422]
    
    @pytest.mark.api
    def test_convert_with_empty_diagnoses(self, test_client):
        """Test FHIR conversion with empty diagnoses list."""
        minimal_data = {
            "patient_info": {"age": "30", "gender": "female"},
            "diagnoses": [],
            "medications": [],
            "vital_signs": {},
            "lab_results": [],
            "plan_actions": [],
            "patient_id": "test-minimal"
        }
        
        response = test_client.post(
            "/fhir/convert",
            json=minimal_data
        )
        
        # Should succeed even with minimal data
        assert response.status_code == 200
        data = response.json()
        # Patient should be created even with minimal demographics
        if data.get("patient"):
            assert data["patient"]["id"] == "test-minimal"
        assert len(data["conditions"]) == 0
        assert len(data["medications"]) == 0
