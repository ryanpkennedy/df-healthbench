#!/usr/bin/env python3
"""
Quick test script for the new /agent/extract_document/{document_id} endpoint.

This script tests extraction by document ID instead of passing full text.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_extract_by_document_id():
    """Test extracting structured data from a document by ID."""
    
    # First, let's get the list of available documents
    print("📋 Fetching available documents...")
    response = requests.get(f"{BASE_URL}/documents")
    response.raise_for_status()
    
    data = response.json()
    document_ids = data.get("document_ids", [])
    count = data.get("count", 0)
    
    print(f"✅ Found {count} documents: {document_ids}\n")
    
    if not document_ids:
        print("❌ No documents found in database. Please seed the database first.")
        return
    
    # Test extraction on the first document
    document_id = document_ids[0]
    print(f"🔍 Testing extraction on document ID: {document_id}")
    print(f"🌐 POST {BASE_URL}/agent/extract_document/{document_id}")
    print("⏳ This may take 30-60 seconds...\n")
    
    response = requests.post(
        f"{BASE_URL}/agent/extract_document/{document_id}",
        timeout=120  # 2 minute timeout for agent processing
    )
    response.raise_for_status()
    
    result = response.json()
    
    # Display results
    print("=" * 80)
    print("✅ EXTRACTION SUCCESSFUL")
    print("=" * 80)
    
    print(f"\n📊 Processing Time: {result.get('processing_time_ms', 0)}ms")
    print(f"🤖 Model Used: {result.get('model_used', 'N/A')}")
    
    # Patient Info
    patient_info = result.get("patient_info", {})
    if patient_info:
        print(f"\n👤 Patient Info:")
        print(f"   - Age: {patient_info.get('age', 'N/A')}")
        print(f"   - Gender: {patient_info.get('gender', 'N/A')}")
    
    # Diagnoses
    diagnoses = result.get("diagnoses", [])
    print(f"\n🏥 Diagnoses ({len(diagnoses)}):")
    for idx, dx in enumerate(diagnoses, 1):
        print(f"   {idx}. {dx['text']}")
        if dx.get('icd10_code'):
            print(f"      ICD-10: {dx['icd10_code']} - {dx['icd10_description']}")
            print(f"      Confidence: {dx['confidence']}")
    
    # Medications
    medications = result.get("medications", [])
    print(f"\n💊 Medications ({len(medications)}):")
    for idx, med in enumerate(medications, 1):
        print(f"   {idx}. {med['text']}")
        if med.get('rxnorm_code'):
            print(f"      RxNorm: {med['rxnorm_code']} - {med['rxnorm_name']}")
            print(f"      Confidence: {med['confidence']}")
    
    # Vital Signs
    vital_signs = result.get("vital_signs", {})
    if vital_signs:
        print(f"\n🩺 Vital Signs:")
        for key, value in vital_signs.items():
            if value:
                print(f"   - {key.replace('_', ' ').title()}: {value}")
    
    # Lab Results
    lab_results = result.get("lab_results", [])
    if lab_results:
        print(f"\n🔬 Lab Results ({len(lab_results)}):")
        for idx, lab in enumerate(lab_results, 1):
            print(f"   {idx}. {lab}")
    
    # Plan Actions
    plan_actions = result.get("plan_actions", [])
    if plan_actions:
        print(f"\n📝 Plan Actions ({len(plan_actions)}):")
        for idx, action in enumerate(plan_actions, 1):
            print(f"   {idx}. {action}")
    
    print("\n" + "=" * 80)
    print("\n✨ Test completed successfully!")
    print(f"\n💡 Tip: You can now just pass document_id={document_id} instead of the full text!")
    print(f"   Much more convenient for working with stored documents.\n")
    
    # Optionally save full JSON
    with open("extraction_by_id_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print("📄 Full result saved to: extraction_by_id_result.json\n")


if __name__ == "__main__":
    try:
        test_extract_by_document_id()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server at http://localhost:8000")
        print("   Make sure the backend is running: poetry run uvicorn app.main:app --reload")
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response is not None:
            print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

