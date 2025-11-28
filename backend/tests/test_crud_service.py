"""
Test script for CRUD and Service layers.

Run this script to verify:
1. CRUD operations work correctly
2. Service layer handles business logic
3. Error handling works as expected
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import create_tables, SessionLocal
from app.schemas.document import DocumentCreate
from app.services.document import DocumentService, DocumentNotFoundError
from app.crud import document as document_crud


def test_crud_operations():
    """Test basic CRUD operations."""
    print("\n" + "=" * 60)
    print("Testing CRUD Operations")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Test 1: Create document
        print("\n1. Testing create_document...")
        doc_data = DocumentCreate(
            title="Test SOAP Note #1",
            content="Subjective: Patient reports headache and fever for 2 days."
        )
        doc = document_crud.create_document(db, doc_data)
        print(f"✅ Created document ID: {doc.id}")
        print(f"   Title: {doc.title}")
        print(f"   Created at: {doc.created_at}")
        
        # Test 2: Get document by ID
        print("\n2. Testing get_document...")
        retrieved_doc = document_crud.get_document(db, doc.id)
        if retrieved_doc and retrieved_doc.id == doc.id:
            print(f"✅ Retrieved document ID: {retrieved_doc.id}")
        else:
            print("❌ Failed to retrieve document")
            return False
        
        # Test 3: Get all document IDs
        print("\n3. Testing get_document_ids...")
        ids = document_crud.get_document_ids(db)
        print(f"✅ Found {len(ids)} document IDs: {ids}")
        
        # Test 4: Get documents with pagination
        print("\n4. Testing get_documents (pagination)...")
        docs = document_crud.get_documents(db, skip=0, limit=10)
        print(f"✅ Retrieved {len(docs)} documents")
        
        # Test 5: Get document count
        print("\n5. Testing get_documents_count...")
        count = document_crud.get_documents_count(db)
        print(f"✅ Total documents: {count}")
        
        # Test 6: Update document
        print("\n6. Testing update_document...")
        updated_doc = document_crud.update_document(
            db, doc.id,
            title="Updated Test SOAP Note"
        )
        if updated_doc and updated_doc.title == "Updated Test SOAP Note":
            print(f"✅ Updated document title: {updated_doc.title}")
        else:
            print("❌ Failed to update document")
            return False
        
        # Test 7: Delete document
        print("\n7. Testing delete_document...")
        success = document_crud.delete_document(db, doc.id)
        if success:
            print(f"✅ Deleted document ID: {doc.id}")
        else:
            print("❌ Failed to delete document")
            return False
        
        # Test 8: Verify deletion
        print("\n8. Verifying deletion...")
        deleted_doc = document_crud.get_document(db, doc.id)
        if deleted_doc is None:
            print("✅ Document successfully deleted (not found)")
        else:
            print("❌ Document still exists after deletion")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ CRUD test failed with error: {e}")
        return False
    finally:
        db.close()


def test_service_layer():
    """Test service layer operations."""
    print("\n" + "=" * 60)
    print("Testing Service Layer")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Test 1: Create document via service
        print("\n1. Testing DocumentService.create_new_document...")
        doc_data = DocumentCreate(
            title="Service Test SOAP Note",
            content="Subjective: Patient reports chest pain and shortness of breath."
        )
        response = DocumentService.create_new_document(db, doc_data)
        print(f"✅ Created document ID: {response.id}")
        print(f"   Title: {response.title}")
        print(f"   Type: {type(response).__name__}")
        
        doc_id = response.id
        
        # Test 2: Get document by ID via service
        print("\n2. Testing DocumentService.get_document_by_id...")
        response = DocumentService.get_document_by_id(db, doc_id)
        print(f"✅ Retrieved document: {response.title}")
        
        # Test 3: Get all document IDs via service
        print("\n3. Testing DocumentService.get_all_document_ids...")
        response = DocumentService.get_all_document_ids(db)
        print(f"✅ Found {response.count} documents")
        print(f"   IDs: {response.document_ids}")
        
        # Test 4: Get all documents via service
        print("\n4. Testing DocumentService.get_all_documents...")
        documents = DocumentService.get_all_documents(db, skip=0, limit=10)
        print(f"✅ Retrieved {len(documents)} documents")
        for doc in documents:
            print(f"   - ID {doc.id}: {doc.title[:50]}...")
        
        # Test 5: Test DocumentNotFoundError
        print("\n5. Testing DocumentNotFoundError handling...")
        try:
            DocumentService.get_document_by_id(db, 999999)
            print("❌ Should have raised DocumentNotFoundError")
            return False
        except DocumentNotFoundError as e:
            print(f"✅ Correctly raised DocumentNotFoundError: {e}")
        
        # Test 6: Delete document via service
        print("\n6. Testing DocumentService.delete_document...")
        DocumentService.delete_document(db, doc_id)
        print(f"✅ Deleted document ID: {doc_id}")
        
        # Test 7: Verify deletion raises error
        print("\n7. Verifying deletion via service...")
        try:
            DocumentService.get_document_by_id(db, doc_id)
            print("❌ Should have raised DocumentNotFoundError")
            return False
        except DocumentNotFoundError:
            print("✅ Document not found after deletion")
        
        return True
        
    except Exception as e:
        print(f"❌ Service test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_multiple_documents():
    """Test handling multiple documents."""
    print("\n" + "=" * 60)
    print("Testing Multiple Documents")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Create multiple documents
        print("\n1. Creating 5 test documents...")
        created_ids = []
        for i in range(1, 6):
            doc_data = DocumentCreate(
                title=f"Test Document #{i}",
                content=f"This is test document number {i} with sufficient content."
            )
            response = DocumentService.create_new_document(db, doc_data)
            created_ids.append(response.id)
            print(f"   ✅ Created document ID: {response.id}")
        
        # Get all IDs
        print("\n2. Retrieving all document IDs...")
        response = DocumentService.get_all_document_ids(db)
        print(f"✅ Total documents: {response.count}")
        
        # Clean up
        print("\n3. Cleaning up test documents...")
        for doc_id in created_ids:
            DocumentService.delete_document(db, doc_id)
        print(f"✅ Deleted {len(created_ids)} test documents")
        
        return True
        
    except Exception as e:
        print(f"❌ Multiple documents test failed: {e}")
        return False
    finally:
        db.close()


def main():
    """Run all tests."""
    print("=" * 60)
    print("DF HealthBench - CRUD & Service Layer Tests")
    print("=" * 60)
    
    # Ensure tables exist
    print("\nEnsuring database tables exist...")
    create_tables()
    print("✅ Database ready")
    
    results = []
    
    # Run tests
    results.append(("CRUD Operations", test_crud_operations()))
    results.append(("Service Layer", test_service_layer()))
    results.append(("Multiple Documents", test_multiple_documents()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<30} {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! Phase 4 is complete.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

