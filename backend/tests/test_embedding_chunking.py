"""
Test script for embedding and chunking services.

This script tests:
1. Document chunking with SOAP notes
2. Embedding generation (single and batch)
3. Integration between chunking and embedding
"""

import sys
import time
from pathlib import Path

# Test 1: Chunking Service
print("=" * 60)
print("Test 1: Document Chunking Service")
print("=" * 60)

try:
    from app.services.chunking import chunk_document, get_chunk_stats
    print("✅ Successfully imported chunking service")
    
    # Load a sample SOAP note
    soap_file = Path("../soap/soap_01.txt")
    if not soap_file.exists():
        print(f"❌ SOAP file not found: {soap_file}")
        sys.exit(1)
    
    with open(soap_file, 'r') as f:
        soap_content = f.read()
    
    print(f"\nOriginal document length: {len(soap_content)} characters")
    
    # Test chunking
    chunks = chunk_document(soap_content, max_chunk_size=800, overlap=50)
    print(f"✅ Document chunked into {len(chunks)} chunks")
    
    # Get statistics
    stats = get_chunk_stats(chunks)
    print(f"\nChunk Statistics:")
    print(f"  Count: {stats['count']}")
    print(f"  Average size: {stats['avg_size']} chars")
    print(f"  Min size: {stats['min_size']} chars")
    print(f"  Max size: {stats['max_size']} chars")
    print(f"  Total chars: {stats['total_chars']} chars")
    
    # Show first chunk
    print(f"\nFirst chunk preview:")
    print(f"  {chunks[0][:200]}...")
    
except Exception as e:
    print(f"❌ Error in chunking test: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Embedding Service
print("\n" + "=" * 60)
print("Test 2: Embedding Service")
print("=" * 60)

try:
    from app.services.embedding import get_embedding_service
    print("✅ Successfully imported embedding service")
    
    # Get singleton instance
    embedding_service = get_embedding_service()
    print(f"✅ Embedding service initialized")
    print(f"   Model: {embedding_service.embedding_model}")
    print(f"   Dimensions: {embedding_service.embedding_dimension}")
    
except Exception as e:
    print(f"❌ Error initializing embedding service: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Single Embedding Generation
print("\n" + "=" * 60)
print("Test 3: Single Embedding Generation")
print("=" * 60)

try:
    test_text = "Patient presents with fever and cough. Temperature is 101F."
    print(f"Test text: {test_text}")
    
    start_time = time.time()
    embedding = embedding_service.generate_embedding(test_text)
    elapsed = (time.time() - start_time) * 1000
    
    print(f"✅ Embedding generated successfully")
    print(f"   Dimensions: {len(embedding)}")
    print(f"   First 5 values: {embedding[:5]}")
    print(f"   Elapsed time: {elapsed:.2f}ms")
    
    # Verify dimensions
    if len(embedding) == 1536:
        print("✅ Embedding has correct dimensions (1536)")
    else:
        print(f"❌ Unexpected embedding dimensions: {len(embedding)}")
        sys.exit(1)
    
except Exception as e:
    print(f"❌ Error generating embedding: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Batch Embedding Generation
print("\n" + "=" * 60)
print("Test 4: Batch Embedding Generation")
print("=" * 60)

try:
    # Use the chunks from Test 1
    print(f"Generating embeddings for {len(chunks)} chunks...")
    
    start_time = time.time()
    embeddings = embedding_service.generate_embeddings_batch(chunks)
    elapsed = (time.time() - start_time) * 1000
    
    print(f"✅ Batch embeddings generated successfully")
    print(f"   Count: {len(embeddings)}")
    print(f"   Dimensions per embedding: {len(embeddings[0])}")
    print(f"   Elapsed time: {elapsed:.2f}ms")
    print(f"   Avg time per chunk: {elapsed / len(chunks):.2f}ms")
    
    # Verify all embeddings have correct dimensions
    all_correct = all(len(emb) == 1536 for emb in embeddings)
    if all_correct:
        print("✅ All embeddings have correct dimensions")
    else:
        print("❌ Some embeddings have incorrect dimensions")
        sys.exit(1)
    
except Exception as e:
    print(f"❌ Error generating batch embeddings: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Integration Test - Chunk and Embed Multiple Documents
print("\n" + "=" * 60)
print("Test 5: Integration Test - Multiple Documents")
print("=" * 60)

try:
    soap_dir = Path("../soap")
    soap_files = list(soap_dir.glob("soap_*.txt"))
    
    if not soap_files:
        print("❌ No SOAP files found")
        sys.exit(1)
    
    print(f"Found {len(soap_files)} SOAP files")
    
    total_chunks = 0
    total_embeddings = 0
    
    for soap_file in soap_files[:3]:  # Test first 3 files
        with open(soap_file, 'r') as f:
            content = f.read()
        
        # Chunk document
        doc_chunks = chunk_document(content, max_chunk_size=800, overlap=50)
        total_chunks += len(doc_chunks)
        
        # Generate embeddings (in smaller batches if needed)
        batch_size = 10
        for i in range(0, len(doc_chunks), batch_size):
            batch = doc_chunks[i:i+batch_size]
            batch_embeddings = embedding_service.generate_embeddings_batch(batch)
            total_embeddings += len(batch_embeddings)
        
        print(f"  {soap_file.name}: {len(doc_chunks)} chunks embedded")
    
    print(f"\n✅ Integration test complete")
    print(f"   Total chunks: {total_chunks}")
    print(f"   Total embeddings: {total_embeddings}")
    
    if total_chunks == total_embeddings:
        print("✅ All chunks successfully embedded")
    else:
        print(f"❌ Mismatch: {total_chunks} chunks but {total_embeddings} embeddings")
        sys.exit(1)
    
except Exception as e:
    print(f"❌ Error in integration test: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nEmbedding and chunking services are working correctly.")
print("Ready to proceed with CRUD and RAG service implementation.")

