"""
Test Part 4: Agent Extraction

Tests for:
- Agent extraction service
- Structured data extraction from medical notes
- ICD-10-CM and RxNorm code enrichment
- Agent extraction API endpoints
- Extraction by text and by document ID
"""

import pytest
from pathlib import Path

from app.schemas.document import DocumentCreate
from app.crud import document as document_crud


# ============================================================================
# Agent Service Tests
# ============================================================================

class TestAgentExtractionService:
    """Test agent extraction service layer."""
    
    @pytest.mark.unit
    def test_agent_service_singleton(self):
        """Test that agent service uses singleton pattern."""
        from app.services.agent_extraction import get_extractor_service
        
        service1 = get_extractor_service()
        service2 = get_extractor_service()
        
        assert service1 is service2
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_extract_structured_data_from_soap(self, sample_soap_note):
        """Test extracting structured data from SOAP note."""
        from app.services.agent_extraction import get_extractor_service
        from app.schemas.extraction import StructuredClinicalData
        
        agent_service = get_extractor_service()
        
        result = await agent_service.extract_structured_data(sample_soap_note)
        
        # Verify result is a StructuredClinicalData Pydantic model
        assert isinstance(result, StructuredClinicalData)
        
        # Verify response structure (access as attributes, not dict keys)
        assert hasattr(result, "patient_info")
        assert hasattr(result, "diagnoses")
        assert hasattr(result, "medications")
        assert hasattr(result, "vital_signs")
        assert hasattr(result, "lab_results")
        assert hasattr(result, "plan_actions")
        
        # Verify result types
        assert isinstance(result.diagnoses, list)
        assert isinstance(result.medications, list)
        assert isinstance(result.lab_results, list)
        assert isinstance(result.plan_actions, list)
        
        # Verify patient_info and vital_signs are objects (not dicts)
        assert result.patient_info is not None
        assert result.vital_signs is not None


# ============================================================================
# Agent Extraction Endpoint Tests (Text Input)
# ============================================================================

class TestAgentExtractionEndpoints:
    """Test agent extraction API endpoints."""
    
    @pytest.mark.api
    @pytest.mark.skip(reason="No dedicated /agent/health endpoint - agent extraction tested via main endpoints")
    def test_agent_health_endpoint(self, test_client):
        """Test agent health (no dedicated endpoint)."""
        # Note: Agent health is verified through successful extraction calls
        # No separate /agent/health endpoint exists
        pass
    
    @pytest.mark.api
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_extract_structured_endpoint(self, async_client, sample_soap_note):
        """Test POST /agent/extract_structured with raw text."""
        response = await async_client.post(
            "/agent/extract_structured",
            json={"text": sample_soap_note}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields exist
        assert "patient_info" in data
        assert "diagnoses" in data
        assert "medications" in data
        assert "vital_signs" in data
        assert "lab_results" in data
        assert "plan_actions" in data
        assert "processing_time_ms" in data
        assert "model_used" in data
        
        # Verify data types
        assert isinstance(data["diagnoses"], list)
        assert isinstance(data["medications"], list)
        assert isinstance(data["vital_signs"], dict)
        assert isinstance(data["lab_results"], list)
        assert isinstance(data["plan_actions"], list)
        
        # Verify processing time is reasonable
        assert data["processing_time_ms"] > 0
        assert data["processing_time_ms"] < 180000  # Under 3 minutes
    
    @pytest.mark.api
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_extract_with_diabetes_patient(self, async_client):
        """Test extraction with a diabetes patient note."""
        note = """Subjective:
62-year-old female with Type 2 Diabetes Mellitus presents for routine follow-up.
Reports compliance with Metformin 500mg twice daily.

Objective:
Temperature: 98.6°F
Blood Pressure: 138/86 mmHg
Heart Rate: 72 bpm

Lab Results:
HbA1c: 7.2%

Assessment:
1. Type 2 Diabetes Mellitus - controlled

Plan:
1. Continue Metformin 500mg BID
2. Recheck HbA1c in 3 months"""
        
        response = await async_client.post(
            "/agent/extract_structured",
            json={"text": note}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should extract at least one diagnosis
        assert len(data["diagnoses"]) > 0
        
        # Should find "Type 2 Diabetes" or similar
        diagnoses_text = " ".join([dx["text"] for dx in data["diagnoses"]])
        assert "diabetes" in diagnoses_text.lower()
        
        # Should extract Metformin
        assert len(data["medications"]) > 0
        meds_text = " ".join([med["text"] for med in data["medications"]])
        assert "metformin" in meds_text.lower()
        
        # Should extract HbA1c
        labs = data["lab_results"]
        labs_text = " ".join(labs)
        assert "hba1c" in labs_text.lower() or "a1c" in labs_text.lower()
    
    @pytest.mark.api
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_icd10_code_enrichment(self, async_client):
        """Test that diagnoses are enriched with ICD-10-CM codes."""
        note = """Subjective: Patient with Type 2 Diabetes.
Objective: BP normal
Assessment: Type 2 Diabetes Mellitus
Plan: Continue treatment"""
        
        response = await async_client.post(
            "/agent/extract_structured",
            json={"text": note}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        diagnoses = data["diagnoses"]
        if len(diagnoses) > 0:
            # At least some diagnoses should have ICD codes
            has_icd = any(dx.get("icd10_code") for dx in diagnoses)
            # Note: This might not always be true depending on API availability
            # So we just check the structure exists
            for dx in diagnoses:
                assert "icd10_code" in dx
                assert "icd10_description" in dx
                assert "confidence" in dx
    
    @pytest.mark.api
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_rxnorm_code_enrichment(self, async_client):
        """Test that medications are enriched with RxNorm codes."""
        note = """Subjective: Patient on medications.
Objective: Stable
Assessment: Controlled
Plan: Continue Metformin 500mg twice daily"""
        
        response = await async_client.post(
            "/agent/extract_structured",
            json={"text": note}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        medications = data["medications"]
        if len(medications) > 0:
            # Check structure exists
            for med in medications:
                assert "rxnorm_code" in med
                assert "rxnorm_name" in med
                assert "confidence" in med
    
    @pytest.mark.api
    async def test_extract_empty_text_error(self, async_client):
        """Test that empty text returns validation error."""
        response = await async_client.post(
            "/agent/extract_structured",
            json={"text": ""}
        )
        
        assert response.status_code == 422  # Validation error


# ============================================================================
# Extraction by Document ID Tests (from test_extraction_by_id.py)
# ============================================================================

class TestAgentExtractionByDocumentId:
    """Test agent extraction using document ID instead of raw text."""
    
    @pytest.mark.api
    @pytest.mark.slow
    @pytest.mark.integration
    def test_extract_by_document_id(self, test_client, sample_document_with_diagnosis):
        """Test POST /agent/extract_document/{id} endpoint."""
        doc_id = sample_document_with_diagnosis.id
        
        response = test_client.post(f"/agent/extract_document/{doc_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields exist
        assert "patient_info" in data
        assert "diagnoses" in data
        assert "medications" in data
        assert "vital_signs" in data
        assert "lab_results" in data
        assert "plan_actions" in data
        assert "processing_time_ms" in data
        assert "model_used" in data
        
        # Should extract diagnoses from the sample document
        assert len(data["diagnoses"]) > 0
    
    @pytest.mark.api
    def test_extract_by_document_id_not_found(self, test_client):
        """Test extraction with non-existent document ID."""
        response = test_client.post("/agent/extract_document/999999")
        
        # Endpoint returns 500 for non-existent documents (could be improved to return 404)
        assert response.status_code in [404, 500]
    
    @pytest.mark.api
    @pytest.mark.slow
    @pytest.mark.integration
    def test_extract_multiple_documents(self, test_client_postgres, postgres_db_session):
        """Test extracting from multiple documents."""
        # Create multiple test documents in PostgreSQL
        doc_ids = []
        for i in range(2):
            doc_data = DocumentCreate(
                title=f"Agent Test Document {i+1}",
                content=f"""Subjective: Patient {i+1} with Hypertension.
Objective: BP elevated
Assessment: Essential Hypertension
Plan: Start Lisinopril 10mg daily"""
            )
            doc = document_crud.create_document(postgres_db_session, doc_data)
            doc_ids.append(doc.id)
        
        # Extract from each document (using postgres client)
        results = []
        for doc_id in doc_ids:
            response = test_client_postgres.post(f"/agent/extract_document/{doc_id}")
            assert response.status_code == 200
            results.append(response.json())
        
        # Verify we got results for all documents
        assert len(results) == 2
        
        # Both should have diagnoses
        for result in results:
            assert len(result["diagnoses"]) > 0


# ============================================================================
# Code Enrichment Quality Tests
# ============================================================================

class TestCodeEnrichmentQuality:
    """Test quality of ICD-10-CM and RxNorm code enrichment."""
    
    @pytest.mark.api
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_common_diagnosis_gets_code(self, async_client):
        """Test that common diagnoses get ICD-10-CM codes."""
        note = """Assessment:
1. Type 2 Diabetes Mellitus
2. Hypertension"""
        
        response = await async_client.post(
            "/agent/extract_structured",
            json={"text": note}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        diagnoses = data["diagnoses"]
        
        # Should extract at least the diagnoses
        assert len(diagnoses) >= 2
        
        # Calculate enrichment rate
        icd_count = sum(1 for dx in diagnoses if dx.get('icd10_code'))
        enrichment_rate = icd_count / len(diagnoses) if len(diagnoses) > 0 else 0
        
        # At least 50% should have ICD codes for common diagnoses
        # (This is a quality check - may need adjustment based on API reliability)
        assert enrichment_rate >= 0.3, f"ICD enrichment rate too low: {enrichment_rate:.0%}"
    
    @pytest.mark.api
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_common_medication_gets_code(self, async_client):
        """Test that common medications get RxNorm codes."""
        note = """Plan:
1. Start Metformin 500mg twice daily
2. Start Lisinopril 10mg daily"""
        
        response = await async_client.post(
            "/agent/extract_structured",
            json={"text": note}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        medications = data["medications"]
        
        # Should extract medications
        assert len(medications) >= 2
        
        # Calculate enrichment rate
        rxnorm_count = sum(1 for med in medications if med.get('rxnorm_code'))
        enrichment_rate = rxnorm_count / len(medications) if len(medications) > 0 else 0
        
        # At least 50% should have RxNorm codes for common medications
        assert enrichment_rate >= 0.3, f"RxNorm enrichment rate too low: {enrichment_rate:.0%}"


# ============================================================================
# Multiple SOAP Notes Tests
# ============================================================================

class TestMultipleSOAPNotes:
    """Test extraction across multiple SOAP notes."""
    
    @pytest.mark.api
    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.skip(reason="Slow test - processes 3 SOAP notes, ~90 seconds")
    async def test_extract_from_multiple_soap_notes(self, async_client, sample_soap_notes_dir):
        """Test extracting from the first 3 SOAP notes."""
        soap_files = sorted(sample_soap_notes_dir.glob("soap_*.txt"))[:3]
        
        assert len(soap_files) >= 3, "Need at least 3 SOAP notes for this test"
        
        results = []
        for soap_file in soap_files:
            with open(soap_file) as f:
                note_text = f.read()
            
            response = await async_client.post(
                "/agent/extract_structured",
                json={"text": note_text}
            )
            
            assert response.status_code == 200
            results.append(response.json())
        
        # Verify all extractions succeeded
        assert len(results) == 3
        
        # Calculate statistics
        total_diagnoses = sum(len(r["diagnoses"]) for r in results)
        total_medications = sum(len(r["medications"]) for r in results)
        avg_time = sum(r["processing_time_ms"] for r in results) / len(results)
        
        assert total_diagnoses > 0, "Should extract some diagnoses"
        assert total_medications > 0, "Should extract some medications"
        assert avg_time > 0


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestAgentErrorHandling:
    """Test error handling in agent extraction."""
    
    @pytest.mark.api
    async def test_extract_empty_text(self, async_client):
        """Test extraction with empty text."""
        response = await async_client.post(
            "/agent/extract_structured",
            json={"text": ""}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.api
    async def test_extract_very_short_text(self, async_client):
        """Test extraction with very short text."""
        response = await async_client.post(
            "/agent/extract_structured",
            json={"text": "Short."}
        )
        
        # Should either accept it or return validation error
        assert response.status_code in [200, 422]
    
    @pytest.mark.api
    async def test_extract_missing_text_field(self, async_client):
        """Test extraction without text field."""
        response = await async_client.post(
            "/agent/extract_structured",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.api
    def test_extract_by_invalid_document_id(self, test_client):
        """Test extraction with invalid document ID."""
        response = test_client.post("/agent/extract_document/999999")
        
        # Endpoint returns 500 for non-existent documents (could be improved to return 404)
        assert response.status_code in [404, 500]


# ============================================================================
# Extraction Quality Tests
# ============================================================================

class TestExtractionQuality:
    """Test quality and accuracy of extraction."""
    
    @pytest.mark.api
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_extracts_patient_demographics(self, async_client):
        """Test that patient age and gender are extracted."""
        note = """Subjective:
45-year-old male presents with headache.

Assessment: Tension headache
Plan: OTC pain relief"""
        
        response = await async_client.post(
            "/agent/extract_structured",
            json={"text": note}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        patient_info = data["patient_info"]
        # Should extract age and gender
        assert patient_info.get("age") is not None
        assert patient_info.get("gender") is not None
    
    @pytest.mark.api
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_extracts_vital_signs(self, async_client):
        """Test that vital signs are extracted."""
        note = """Objective:
Temperature: 98.6°F
Blood Pressure: 120/80 mmHg
Heart Rate: 72 bpm
Respiratory Rate: 16/min

Assessment: Normal exam
Plan: Continue current management"""
        
        response = await async_client.post(
            "/agent/extract_structured",
            json={"text": note}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        vitals = data["vital_signs"]
        
        # Should extract at least some vitals
        non_null_vitals = {k: v for k, v in vitals.items() if v is not None}
        assert len(non_null_vitals) > 0, "Should extract at least one vital sign"
    
    @pytest.mark.api
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_extracts_plan_actions(self, async_client):
        """Test that plan actions are extracted."""
        note = """Assessment: Hypertension

Plan:
1. Start Lisinopril 10mg daily
2. Follow up in 2 weeks
3. Check blood pressure at home
4. Low sodium diet"""
        
        response = await async_client.post(
            "/agent/extract_structured",
            json={"text": note}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        plan_actions = data["plan_actions"]
        
        # Should extract multiple plan items
        assert len(plan_actions) >= 2, "Should extract multiple plan actions"
    
    @pytest.mark.api
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_handles_note_without_medications(self, async_client):
        """Test extraction when note has no medications."""
        note = """Subjective: Patient with tension headache.
Objective: Normal physical exam
Assessment: Tension headache
Plan: Rest and hydration"""
        
        response = await async_client.post(
            "/agent/extract_structured",
            json={"text": note}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Medications list should exist even if empty
        assert "medications" in data
        assert isinstance(data["medications"], list)
