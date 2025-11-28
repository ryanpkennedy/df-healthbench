"""
Complete Part 1 Verification Script

This script tests all components of Part 1: Backend Foundation
to ensure everything is working correctly before moving to Part 2.
"""

import sys
from pathlib import Path
import requests
import time

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import create_tables, SessionLocal, check_db_connection
from app.schemas.document import DocumentCreate
from app.services.document import DocumentService


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_database():
    """Test database setup and connection."""
    print_section("Testing Database Setup")
    
    results = []
    
    # Test 1: Database connection
    print("\n1. Testing database connection...")
    if check_db_connection():
        print("   ✅ Database connected successfully")
        results.append(True)
    else:
        print("   ❌ Database connection failed")
        results.append(False)
        return False  # Can't continue without DB
    
    # Test 2: Create tables
    print("\n2. Creating database tables...")
    try:
        create_tables()
        print("   ✅ Tables created successfully")
        results.append(True)
    except Exception as e:
        print(f"   ❌ Failed to create tables: {e}")
        results.append(False)
        return False
    
    # Test 3: CRUD operations
    print("\n3. Testing CRUD operations...")
    db = SessionLocal()
    try:
        doc_data = DocumentCreate(
            title="Verification Test Document",
            content="This is a test document for Part 1 verification."
        )
        doc = DocumentService.create_new_document(db, doc_data)
        print(f"   ✅ Created document ID: {doc.id}")
        
        retrieved = DocumentService.get_document_by_id(db, doc.id)
        print(f"   ✅ Retrieved document: {retrieved.title}")
        
        DocumentService.delete_document(db, doc.id)
        print(f"   ✅ Deleted document ID: {doc.id}")
        
        results.append(True)
    except Exception as e:
        print(f"   ❌ CRUD operations failed: {e}")
        results.append(False)
    finally:
        db.close()
    
    return all(results)


def test_api_endpoints():
    """Test API endpoints (requires server to be running)."""
    print_section("Testing API Endpoints")
    
    base_url = "http://localhost:8000"
    
    print("\nℹ️  This test requires the server to be running.")
    print("   Start server: poetry run uvicorn app.main:app --reload")
    print("\nChecking if server is running...")
    
    try:
        response = requests.get(f"{base_url}/", timeout=2)
        print(f"   ✅ Server is running (status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("   ⚠️  Server is not running - skipping API tests")
        print("   Start the server and run this test again to verify API endpoints")
        return None
    
    results = []
    
    # Test 1: Root endpoint
    print("\n1. Testing root endpoint (GET /)...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Root endpoint working")
            print(f"      API: {data.get('name')} v{data.get('version')}")
            results.append(True)
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
            results.append(False)
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results.append(False)
    
    # Test 2: Health check
    print("\n2. Testing health endpoint (GET /health)...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200 and response.json().get("status") == "ok":
            print("   ✅ Health check passed")
            results.append(True)
        else:
            print(f"   ❌ Health check failed: {response.json()}")
            results.append(False)
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results.append(False)
    
    # Test 3: Health check with DB
    print("\n3. Testing health with DB (GET /health/db)...")
    try:
        response = requests.get(f"{base_url}/health/db")
        if response.status_code == 200:
            data = response.json()
            db_status = data.get("database")
            if db_status == "connected":
                print(f"   ✅ Database health check passed")
                results.append(True)
            else:
                print(f"   ❌ Database not connected: {db_status}")
                results.append(False)
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
            results.append(False)
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results.append(False)
    
    # Test 4: Get documents
    print("\n4. Testing get documents (GET /documents)...")
    try:
        response = requests.get(f"{base_url}/documents")
        if response.status_code == 200:
            data = response.json()
            count = data.get("count", 0)
            print(f"   ✅ Retrieved {count} documents")
            if count > 0:
                print(f"      Document IDs: {data.get('document_ids', [])}")
            results.append(True)
        else:
            print(f"   ❌ Failed: {response.status_code}")
            results.append(False)
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results.append(False)
    
    # Test 5: Create document
    print("\n5. Testing create document (POST /documents)...")
    try:
        doc_data = {
            "title": "API Test Document",
            "content": "This is a test document created via the API to verify POST endpoint functionality."
        }
        response = requests.post(f"{base_url}/documents", json=doc_data)
        if response.status_code == 201:
            data = response.json()
            doc_id = data.get("id")
            print(f"   ✅ Created document ID: {doc_id}")
            
            # Test 6: Get specific document
            print(f"\n6. Testing get document by ID (GET /documents/{doc_id})...")
            response = requests.get(f"{base_url}/documents/{doc_id}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Retrieved document: {data.get('title')}")
                results.append(True)
            else:
                print(f"   ❌ Failed to retrieve: {response.status_code}")
                results.append(False)
            
            # Test 7: Delete document
            print(f"\n7. Testing delete document (DELETE /documents/{doc_id})...")
            response = requests.delete(f"{base_url}/documents/{doc_id}")
            if response.status_code == 204:
                print(f"   ✅ Deleted document ID: {doc_id}")
                results.append(True)
            else:
                print(f"   ❌ Failed to delete: {response.status_code}")
                results.append(False)
            
            results.append(True)
        else:
            print(f"   ❌ Failed to create: {response.status_code}")
            results.append(False)
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results.append(False)
    
    # Test 8: Swagger docs
    print("\n8. Testing API documentation (GET /docs)...")
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("   ✅ Swagger UI accessible at http://localhost:8000/docs")
            results.append(True)
        else:
            print(f"   ❌ Docs not accessible: {response.status_code}")
            results.append(False)
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results.append(False)
    
    return all(results)


def test_seed_data():
    """Test database seeding."""
    print_section("Testing Database Seeding")
    
    print("\n1. Checking for SOAP notes...")
    soap_dir = Path(__file__).parent.parent / "soap"
    
    if not soap_dir.exists():
        print(f"   ⚠️  SOAP directory not found: {soap_dir}")
        return None
    
    soap_files = list(soap_dir.glob("soap_*.txt"))
    print(f"   ✅ Found {len(soap_files)} SOAP note files")
    
    print("\n2. Verifying seeded documents...")
    db = SessionLocal()
    try:
        response = DocumentService.get_all_document_ids(db)
        count = response.count
        
        if count >= len(soap_files):
            print(f"   ✅ Database contains {count} documents (expected at least {len(soap_files)})")
            return True
        else:
            print(f"   ⚠️  Database contains {count} documents (expected {len(soap_files)})")
            print("   Run: poetry run python -m app.seed --force")
            return False
    except Exception as e:
        print(f"   ❌ Failed to check seed data: {e}")
        return False
    finally:
        db.close()


def main():
    """Run all verification tests."""
    print("=" * 70)
    print("  DF HEALTHBENCH - PART 1 COMPLETE VERIFICATION")
    print("=" * 70)
    print("\nThis script verifies all components of Part 1: Backend Foundation")
    
    results = {}
    
    # Test database
    results["Database"] = test_database()
    
    # Test seed data
    results["Seed Data"] = test_seed_data()
    
    # Test API endpoints
    results["API Endpoints"] = test_api_endpoints()
    
    # Summary
    print_section("VERIFICATION SUMMARY")
    
    for component, result in results.items():
        if result is True:
            status = "✅ PASSED"
        elif result is False:
            status = "❌ FAILED"
        else:
            status = "⚠️  SKIPPED"
        print(f"{component:<30} {status}")
    
    # Overall result
    print("\n" + "=" * 70)
    
    passed = [r for r in results.values() if r is True]
    failed = [r for r in results.values() if r is False]
    skipped = [r for r in results.values() if r is None]
    
    print(f"Results: {len(passed)} passed, {len(failed)} failed, {len(skipped)} skipped")
    
    if len(failed) == 0:
        print("\n🎉 Part 1: Backend Foundation is COMPLETE!")
        print("\nYou can now proceed to Part 2: LLM API Integration")
        print("\nNext steps:")
        print("  1. Set up OpenAI API key in .env file")
        print("  2. Implement POST /summarize_note endpoint")
        print("  3. Add LLM-based document summarization")
    else:
        print("\n⚠️  Some components failed verification.")
        print("Please fix the issues above before proceeding to Part 2.")
    
    print("=" * 70)
    
    return 0 if len(failed) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

