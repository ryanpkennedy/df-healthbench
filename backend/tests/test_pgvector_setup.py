"""
Test script to verify PGVector setup and DocumentEmbedding model.

This script tests:
1. PGVector extension is enabled
2. DocumentEmbedding model can be imported
3. document_embeddings table can be created
4. Vector operations work correctly
"""

import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Test 1: Check PGVector extension
print("=" * 60)
print("Test 1: Checking PGVector Extension")
print("=" * 60)

try:
    engine = create_engine("postgresql://dfuser:dfpassword@localhost:5432/df_healthbench")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"))
        row = result.fetchone()
        if row:
            print(f"✅ PGVector extension enabled: version {row[1]}")
        else:
            print("❌ PGVector extension NOT found")
            sys.exit(1)
except Exception as e:
    print(f"❌ Error checking extension: {e}")
    sys.exit(1)

# Test 2: Import DocumentEmbedding model
print("\n" + "=" * 60)
print("Test 2: Importing DocumentEmbedding Model")
print("=" * 60)

try:
    from app.models.document_embedding import DocumentEmbedding
    from app.models.document import Document
    print("✅ Successfully imported DocumentEmbedding model")
    print(f"   Table name: {DocumentEmbedding.__tablename__}")
    print(f"   Columns: {[c.name for c in DocumentEmbedding.__table__.columns]}")
except Exception as e:
    print(f"❌ Error importing model: {e}")
    sys.exit(1)

# Test 3: Create tables
print("\n" + "=" * 60)
print("Test 3: Creating Database Tables")
print("=" * 60)

try:
    from app.database import Base, engine
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")
    
    # Verify table exists
    with engine.connect() as conn:
        result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public';"))
        tables = [row[0] for row in result.fetchall()]
        print(f"   Tables in database: {tables}")
        
        if 'document_embeddings' in tables:
            print("✅ document_embeddings table exists")
        else:
            print("❌ document_embeddings table NOT found")
            sys.exit(1)
            
except Exception as e:
    print(f"❌ Error creating tables: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Verify vector column
print("\n" + "=" * 60)
print("Test 4: Verifying Vector Column")
print("=" * 60)

try:
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'document_embeddings';
        """))
        columns = result.fetchall()
        print("   Columns in document_embeddings:")
        for col in columns:
            print(f"     - {col[0]}: {col[1]} ({col[2]})")
        
        # Check for vector column
        vector_col = [c for c in columns if c[2] == 'vector']
        if vector_col:
            print(f"✅ Vector column found: {vector_col[0][0]}")
        else:
            print("❌ Vector column NOT found")
            sys.exit(1)
            
except Exception as e:
    print(f"❌ Error verifying columns: {e}")
    sys.exit(1)

# Test 5: Test vector operations
print("\n" + "=" * 60)
print("Test 5: Testing Vector Operations")
print("=" * 60)

try:
    from app.database import SessionLocal
    import numpy as np
    
    db = SessionLocal()
    
    # Create a test embedding (1536 dimensions for text-embedding-3-small)
    test_embedding = np.random.rand(1536).tolist()
    
    # Create a test document first
    from app.models.document import Document
    test_doc = Document(
        title="Test Document for Embedding",
        content="This is a test document to verify vector operations work correctly."
    )
    db.add(test_doc)
    db.commit()
    db.refresh(test_doc)
    print(f"✅ Created test document with ID: {test_doc.id}")
    
    # Create a test embedding
    test_embedding_obj = DocumentEmbedding(
        document_id=test_doc.id,
        chunk_index=0,
        chunk_text="This is a test chunk.",
        embedding=test_embedding
    )
    db.add(test_embedding_obj)
    db.commit()
    db.refresh(test_embedding_obj)
    print(f"✅ Created test embedding with ID: {test_embedding_obj.id}")
    
    # Query it back
    retrieved = db.query(DocumentEmbedding).filter(DocumentEmbedding.id == test_embedding_obj.id).first()
    if retrieved:
        print(f"✅ Successfully retrieved embedding")
        print(f"   Document ID: {retrieved.document_id}")
        print(f"   Chunk index: {retrieved.chunk_index}")
        print(f"   Chunk text: {retrieved.chunk_text[:50]}...")
        print(f"   Embedding dimensions: {len(retrieved.embedding)}")
    else:
        print("❌ Failed to retrieve embedding")
        sys.exit(1)
    
    # Clean up test data
    db.delete(retrieved)
    db.delete(test_doc)
    db.commit()
    print("✅ Cleaned up test data")
    
    db.close()
    
except Exception as e:
    print(f"❌ Error testing vector operations: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nPGVector setup is complete and working correctly.")
print("You can now proceed with implementing the RAG pipeline.")

