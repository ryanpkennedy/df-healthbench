"""
Test script to verify database configuration and models.

Run this script to ensure:
1. Database connection is working
2. Tables can be created successfully
3. Models and schemas are properly configured
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import check_db_connection, create_tables, SessionLocal
from app.models import Document
from app.schemas import DocumentCreate, DocumentResponse


def test_db_connection():
    """Test database connection."""
    print("Testing database connection...")
    if check_db_connection():
        print("✅ Database connection successful!")
        return True
    else:
        print("❌ Database connection failed!")
        print("Make sure PostgreSQL is running: make db-start")
        return False


def test_create_tables():
    """Test table creation."""
    print("\nCreating database tables...")
    try:
        create_tables()
        print("✅ Tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False


def test_insert_document():
    """Test inserting a document."""
    print("\nTesting document insertion...")
    try:
        db = SessionLocal()
        
        # Create a test document
        doc = Document(
            title="Test SOAP Note",
            content="Subjective: Test patient reports test symptoms."
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        print(f"✅ Document created with ID: {doc.id}")
        print(f"   Title: {doc.title}")
        print(f"   Created at: {doc.created_at}")
        
        # Clean up - delete test document
        db.delete(doc)
        db.commit()
        db.close()
        
        return True
    except Exception as e:
        print(f"❌ Failed to insert document: {e}")
        return False


def test_schemas():
    """Test Pydantic schemas."""
    print("\nTesting Pydantic schemas...")
    try:
        # Test DocumentCreate validation
        doc_create = DocumentCreate(
            title="Test Document",
            content="This is test content with at least 10 characters."
        )
        print(f"✅ DocumentCreate schema validated")
        print(f"   Title: {doc_create.title}")
        print(f"   Content length: {len(doc_create.content)} chars")
        
        # Test validation error for short content
        try:
            invalid_doc = DocumentCreate(title="Test", content="Short")
            print("❌ Validation should have failed for short content")
            return False
        except Exception:
            print("✅ Validation correctly rejected short content")
        
        return True
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("DF HealthBench - Database Setup Test")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Database Connection", test_db_connection()))
    results.append(("Table Creation", test_create_tables()))
    results.append(("Document Insertion", test_insert_document()))
    results.append(("Schema Validation", test_schemas()))
    
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
        print("🎉 All tests passed! Phase 3 setup is complete.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

