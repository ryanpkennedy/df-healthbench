"""
Test script for agent extraction API endpoint.

Tests the POST /agent/extract_structured endpoint with SOAP notes.
"""

import asyncio
import httpx
from pathlib import Path
import json


async def test_extraction_endpoint(soap_file: str, base_url: str = "http://localhost:8000"):
    """
    Test the extraction endpoint with a SOAP note.
    
    Args:
        soap_file: Path to SOAP note file
        base_url: Base URL of the API
    """
    # Load SOAP note
    soap_path = Path(soap_file)
    if not soap_path.exists():
        print(f"❌ File not found: {soap_file}")
        return None
    
    with open(soap_path, "r") as f:
        note_text = f.read()
    
    print(f"\n{'='*80}")
    print(f"Testing: {soap_path.name}")
    print(f"{'='*80}")
    print(f"Note length: {len(note_text)} characters")
    
    # Make request
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            print("⏳ Sending request to agent extraction endpoint...")
            response = await client.post(
                f"{base_url}/agent/extract_structured",
                json={"text": note_text}
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Display results
            print(f"\n✅ Extraction successful!")
            print(f"   Processing time: {result['processing_time_ms']}ms")
            print(f"   Model used: {result['model_used']}")
            
            # Patient info
            if result.get('patient_info'):
                patient = result['patient_info']
                if patient.get('age') or patient.get('gender'):
                    print(f"\n👤 Patient Info:")
                    if patient.get('age'):
                        print(f"   Age: {patient['age']}")
                    if patient.get('gender'):
                        print(f"   Gender: {patient['gender']}")
            
            # Diagnoses
            diagnoses = result.get('diagnoses', [])
            print(f"\n🏥 Diagnoses: {len(diagnoses)}")
            for dx in diagnoses:
                print(f"   • {dx['text']}")
                if dx.get('icd10_code'):
                    print(f"     └─ ICD-10: {dx['icd10_code']} - {dx['icd10_description']}")
                    print(f"        Confidence: {dx['confidence']}")
                else:
                    print(f"     └─ No ICD code found")
            
            # Medications
            medications = result.get('medications', [])
            print(f"\n💊 Medications: {len(medications)}")
            for med in medications:
                print(f"   • {med['text']}")
                if med.get('rxnorm_code'):
                    print(f"     └─ RxNorm: {med['rxnorm_code']} - {med['rxnorm_name']}")
                    print(f"        Confidence: {med['confidence']}")
                else:
                    print(f"     └─ No RxNorm code found")
            
            # Vital signs
            vitals = result.get('vital_signs')
            if vitals:
                vital_count = sum(1 for v in vitals.values() if v is not None)
                if vital_count > 0:
                    print(f"\n📈 Vital Signs: {vital_count}")
                    for key, value in vitals.items():
                        if value:
                            print(f"   • {key.replace('_', ' ').title()}: {value}")
            
            # Lab results
            labs = result.get('lab_results', [])
            if labs:
                print(f"\n🔬 Lab Results: {len(labs)}")
                for lab in labs:
                    print(f"   • {lab}")
            
            # Plan actions
            plans = result.get('plan_actions', [])
            if plans:
                print(f"\n📋 Plan Actions: {len(plans)}")
                for plan in plans:
                    print(f"   • {plan}")
            
            # Code enrichment summary
            icd_count = sum(1 for dx in diagnoses if dx.get('icd10_code'))
            rxnorm_count = sum(1 for med in medications if med.get('rxnorm_code'))
            
            print(f"\n📊 Code Enrichment:")
            print(f"   • {icd_count}/{len(diagnoses)} diagnoses have ICD-10-CM codes")
            print(f"   • {rxnorm_count}/{len(medications)} medications have RxNorm codes")
            
            return result
            
        except httpx.HTTPStatusError as e:
            print(f"\n❌ HTTP Error: {e.response.status_code}")
            print(f"   {e.response.json()}")
            return None
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return None


async def test_health_endpoint(base_url: str = "http://localhost:8000"):
    """Test the health endpoint."""
    print(f"\n{'='*80}")
    print("Testing Health Endpoint")
    print(f"{'='*80}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{base_url}/agent/health")
            response.raise_for_status()
            result = response.json()
            print(f"✅ Service is healthy")
            print(f"   Status: {result['status']}")
            print(f"   Agent: {result['agent_name']}")
            print(f"   Tools: {result['tools_count']}")
            return True
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False


async def main():
    """Main test function."""
    print(f"\n{'='*80}")
    print("AGENT EXTRACTION API TESTING")
    print(f"{'='*80}")
    
    # Test health endpoint first
    if not await test_health_endpoint():
        print("\n❌ Service not ready. Make sure the server is running:")
        print("   poetry run uvicorn app.main:app --reload")
        return
    
    # Test SOAP notes
    soap_dir = Path("../med_docs/soap")
    if not soap_dir.exists():
        soap_dir = Path("../../med_docs/soap")
    
    if not soap_dir.exists():
        print(f"\n❌ SOAP notes directory not found")
        return
    
    # Test first 3 SOAP notes
    soap_files = sorted(soap_dir.glob("soap_*.txt"))[:3]
    
    if not soap_files:
        print(f"\n❌ No SOAP notes found in {soap_dir}")
        return
    
    results = []
    for soap_file in soap_files:
        result = await test_extraction_endpoint(str(soap_file))
        if result:
            results.append((soap_file.name, result))
    
    # Summary
    print(f"\n{'='*80}")
    print("TESTING SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Successfully tested {len(results)}/{len(soap_files)} SOAP notes")
    
    if results:
        avg_time = sum(r[1]['processing_time_ms'] for r in results) / len(results)
        total_diagnoses = sum(len(r[1]['diagnoses']) for r in results)
        total_medications = sum(len(r[1]['medications']) for r in results)
        total_icd = sum(sum(1 for dx in r[1]['diagnoses'] if dx.get('icd10_code')) for r in results)
        total_rxnorm = sum(sum(1 for med in r[1]['medications'] if med.get('rxnorm_code')) for r in results)
        
        print(f"\n📊 Overall Statistics:")
        print(f"   • Average processing time: {avg_time:.0f}ms")
        print(f"   • Total diagnoses extracted: {total_diagnoses}")
        print(f"   • Total medications extracted: {total_medications}")
        print(f"   • ICD-10-CM enrichment rate: {total_icd}/{total_diagnoses} ({100*total_icd/total_diagnoses if total_diagnoses else 0:.0f}%)")
        print(f"   • RxNorm enrichment rate: {total_rxnorm}/{total_medications} ({100*total_rxnorm/total_medications if total_medications else 0:.0f}%)")


if __name__ == "__main__":
    asyncio.run(main())

