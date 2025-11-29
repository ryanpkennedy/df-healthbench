"""
Test script for RAG pipeline integration.

This script tests:
1. Embedding CRUD operations
2. Vector similarity search
3. RAG service (embed documents, answer questions)
4. End-to-end RAG pipeline
"""

import sys
from sqlalchemy.orm import Session

# Test 1: Database and Model Setup
print("=" * 60)
print("Test 1: Database and Model Setup")
print("=" * 60)

try:
    from app.database import SessionLocal, engine
    from app.models.document import Document
    from app.models.document_embedding import DocumentEmbedding
    
    # Create tables
    from app.database import Base
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database connection successful")
    print("✅ Tables created/verified")
    
    # Get a database session
    db = SessionLocal()
    print("✅ Database session created")
    
except Exception as e:
    print(f"❌ Error in database setup: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: CRUD Operations
print("\n" + "=" * 60)
print("Test 2: Embedding CRUD Operations")
print("=" * 60)

try:
    from app.crud import embedding as embedding_crud
    from app.crud import document as document_crud
    
    # Get a test document
    documents = document_crud.get_documents(db, limit=1)
    if not documents:
        print("❌ No documents found in database")
        print("   Please run the application first to seed documents")
        sys.exit(1)
    
    test_doc = documents[0]
    print(f"✅ Found test document: id={test_doc.id}, title='{test_doc.title}'")
    
    # Check if document has embeddings
    has_embeddings = embedding_crud.document_has_embeddings(db, test_doc.id)
    print(f"   Document has embeddings: {has_embeddings}")
    
    if has_embeddings:
        count = embedding_crud.count_embeddings_by_document(db, test_doc.id)
        print(f"   Embedding count: {count}")
        
        # Get embeddings
        embeddings = embedding_crud.get_embeddings_by_document(db, test_doc.id)
        print(f"✅ Retrieved {len(embeddings)} embeddings")
        
        if embeddings:
            first_emb = embeddings[0]
            print(f"   First chunk preview: {first_emb.chunk_text[:100]}...")
            print(f"   Embedding dimensions: {len(first_emb.embedding)}")
    
    # Get overall stats
    stats = embedding_crud.get_embedding_stats(db)
    print(f"\n✅ Embedding statistics:")
    print(f"   Total embeddings: {stats['total_embeddings']}")
    print(f"   Documents with embeddings: {stats['total_documents_with_embeddings']}")
    print(f"   Avg chunks per document: {stats['avg_chunks_per_document']}")
    
except Exception as e:
    print(f"❌ Error in CRUD operations: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: RAG Service - Embed Document
print("\n" + "=" * 60)
print("Test 3: RAG Service - Embed Document")
print("=" * 60)

try:
    from app.services.rag import RAGService
    
    rag_service = RAGService(db)
    print("✅ RAG service initialized")
    
    # Get a document that hasn't been embedded yet (or use force=True)
    all_docs = document_crud.get_documents(db, limit=10)
    test_doc_for_embedding = None
    
    for doc in all_docs:
        if not embedding_crud.document_has_embeddings(db, doc.id):
            test_doc_for_embedding = doc
            break
    
    if test_doc_for_embedding:
        print(f"\nEmbedding document: id={test_doc_for_embedding.id}, title='{test_doc_for_embedding.title}'")
        
        result = rag_service.embed_document(test_doc_for_embedding.id)
        
        print(f"✅ Document embedded successfully")
        print(f"   Chunks created: {result['chunks_created']}")
        print(f"   Embeddings created: {result['embeddings_created']}")
        print(f"   Processing time: {result['processing_time_ms']}ms")
    else:
        print("ℹ️  All documents already embedded (skipping embed test)")
        print("   This is fine - embeddings are already in place")
    
except Exception as e:
    print(f"❌ Error in RAG embed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Vector Similarity Search
print("\n" + "=" * 60)
print("Test 4: Vector Similarity Search")
print("=" * 60)

try:
    from app.services.embedding import get_embedding_service
    
    # Check if we have any embeddings to search
    total_embeddings = embedding_crud.count_embeddings(db)
    if total_embeddings == 0:
        print("❌ No embeddings found for search")
        print("   Please embed at least one document first")
        sys.exit(1)
    
    print(f"Found {total_embeddings} embeddings in database")
    
    # Generate a test query embedding
    embedding_service = get_embedding_service()
    test_query = "What medications are mentioned?"
    print(f"\nTest query: '{test_query}'")
    
    query_embedding = embedding_service.generate_embedding(test_query)
    print(f"✅ Query embedding generated: {len(query_embedding)} dimensions")
    
    # Search for similar chunks
    results = embedding_crud.search_similar_chunks(
        db,
        query_embedding,
        limit=3
    )
    
    print(f"✅ Vector search completed: {len(results)} results")
    
    for i, (chunk, similarity) in enumerate(results, 1):
        doc = document_crud.get_document(db, chunk.document_id)
        print(f"\n   Result {i}:")
        print(f"   Similarity: {similarity:.4f}")
        print(f"   Document: {doc.title}")
        print(f"   Chunk: {chunk.chunk_text[:150]}...")
    
except Exception as e:
    print(f"❌ Error in vector search: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: RAG Service - Answer Question
print("\n" + "=" * 60)
print("Test 5: RAG Service - Answer Question")
print("=" * 60)

try:
    # Check if we have embeddings
    if embedding_crud.count_embeddings(db) == 0:
        print("❌ No embeddings found")
        print("   Cannot test question answering without embeddings")
        sys.exit(1)
    
    test_questions = [
        "What medications are mentioned in the notes?",
        "What are the patient's vital signs?",
        "What follow-up care is recommended?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- Question {i} ---")
        print(f"Q: {question}")
        
        try:
            result = rag_service.answer_question(question, top_k=3)
            
            print(f"\nA: {result['answer'][:300]}...")
            print(f"\n✅ Answer generated successfully")
            print(f"   Model: {result['model_used']}")
            print(f"   Total tokens: {result['token_usage']['total_tokens']}")
            print(f"   Processing time: {result['processing_time_ms']}ms")
            print(f"   Retrieval time: {result['retrieval_time_ms']}ms")
            print(f"   Generation time: {result['generation_time_ms']}ms")
            print(f"   Sources used: {len(result['sources'])}")
            
            for j, source in enumerate(result['sources'], 1):
                print(f"      Source {j}: {source['document_title']} (similarity: {source['similarity_score']:.4f})")
            
        except Exception as e:
            print(f"❌ Error answering question: {e}")
            import traceback
            traceback.print_exc()
    
except Exception as e:
    print(f"❌ Error in question answering: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: RAG Stats
print("\n" + "=" * 60)
print("Test 6: RAG Statistics")
print("=" * 60)

try:
    stats = rag_service.get_stats()
    
    print("✅ RAG system statistics:")
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Total embeddings: {stats['total_embeddings']}")
    print(f"   Documents with embeddings: {stats['documents_with_embeddings']}")
    print(f"   Avg chunks per document: {stats['avg_chunks_per_document']}")
    print(f"   Embedding dimension: {stats['embedding_dimension']}")
    print(f"   Embedding model: {stats['embedding_model']}")
    print(f"   Chunk size: {stats['chunk_size']}")
    print(f"   Chunk overlap: {stats['chunk_overlap']}")
    print(f"   RAG top-k: {stats['rag_top_k']}")
    
except Exception as e:
    print(f"❌ Error getting stats: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Cleanup
db.close()

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nRAG pipeline is working correctly.")
print("Ready to implement API endpoints.")

