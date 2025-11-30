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
    
    assert extraction_response.status_code == 200, f"Extraction failed: {extraction_response.text}"
    structured_data = extraction_response.json()
    
    print(f"✅ Extracted {len(structured_data['diagnoses'])} diagnoses")
    print(f"✅ Extracted {len(structured_data['medications'])} medications")
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
    
    assert fhir_response.status_code == 200, f"FHIR conversion failed: {fhir_response.text}"
    fhir_resources = fhir_response.json()
    
    # 4. Validate FHIR resources
    print(f"✅ Created {fhir_resources['resource_count']} FHIR resources:")
    print(f"  - Patient: {1 if fhir_resources['patient'] else 0}")
    print(f"  - Conditions: {len(fhir_resources['conditions'])}")
    print(f"  - Medications: {len(fhir_resources['medications'])}")
    print(f"  - Observations: {len(fhir_resources['observations'])}")
    print()
    
    # 5. Validate structure
    if fhir_resources["patient"]:
        assert fhir_resources["patient"]["resourceType"] == "Patient"
        print("✅ Patient resource validated")
    
    for condition in fhir_resources["conditions"]:
        assert condition["resourceType"] == "Condition"
        assert "code" in condition
        assert "subject" in condition
        assert "clinicalStatus" in condition
    print(f"✅ {len(fhir_resources['conditions'])} Condition resource(s) validated")
    
    for med in fhir_resources["medications"]:
        assert med["resourceType"] == "MedicationRequest"
        assert "medication" in med
        assert "subject" in med
    print(f"✅ {len(fhir_resources['medications'])} MedicationRequest resource(s) validated")
    
    for obs in fhir_resources["observations"]:
        assert obs["resourceType"] == "Observation"
        assert "code" in obs
        assert "subject" in obs
    print(f"✅ {len(fhir_resources['observations'])} Observation resource(s) validated")
    
    print()
    print("=" * 80)
    print("✅ All FHIR resources validated successfully!")
    print("=" * 80)
    print()
    
    # 6. Pretty print first Condition (if available)
    if fhir_resources["conditions"]:
        print("=" * 80)
        print("EXAMPLE: First Condition Resource")
        print("=" * 80)
        print(json.dumps(fhir_resources["conditions"][0], indent=2))
        print()
    
    # 7. Pretty print first Medication (if available)
    if fhir_resources["medications"]:
        print("=" * 80)
        print("EXAMPLE: First MedicationRequest Resource")
        print("=" * 80)
        print(json.dumps(fhir_resources["medications"][0], indent=2))
    
    return fhir_resources


def test_fhir_health():
    """Test FHIR service health endpoint."""
    
    base_url = "http://localhost:8000"
    
    print("\n" + "=" * 80)
    print("Testing FHIR health endpoint")
    print("=" * 80)
    
    response = httpx.get(f"{base_url}/fhir/health", timeout=5.0)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["service"] == "FHIR Conversion"
    assert data["fhir_version"] == "R4"
    
    print("✅ FHIR health check passed")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("FHIR CONVERSION INTEGRATION TEST")
    print("=" * 80)
    print()
    
    # Test health endpoint first
    test_fhir_health()
    
    # Test full pipeline
    test_full_pipeline_soap_01()
    
    print("\n" + "=" * 80)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 80)

