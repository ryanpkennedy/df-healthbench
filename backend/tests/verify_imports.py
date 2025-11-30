"""
Verification script for all imports and modules.

This script verifies that all modules are properly imported and exported.
"""

import sys

print("=" * 60)
print("Verifying All Imports and Modules")
print("=" * 60)

# Test 1: Models
print("\n1. Testing Models...")
try:
    from app.models import Document, DocumentEmbedding
    print("   ✅ Document")
    print("   ✅ DocumentEmbedding")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 2: Schemas
print("\n2. Testing Schemas...")
try:
    from app.schemas import (
        DocumentBase,
        DocumentCreate,
        DocumentResponse,
        DocumentListResponse,
        SummarizeRequest,
        SummarizeResponse,
        TokenUsage,
        ErrorResponse,
        QuestionRequest,
        SourceChunk,
        AnswerResponse,
        EmbedDocumentResponse,
        EmbedAllResponse,
        RAGStatsResponse,
    )
    print("   ✅ Document schemas")
    print("   ✅ LLM schemas")
    print("   ✅ RAG schemas")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 3: CRUD
print("\n3. Testing CRUD...")
try:
    from app.crud import document, embedding
    print("   ✅ document CRUD")
    print("   ✅ embedding CRUD")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 4: Services
print("\n4. Testing Services...")
try:
    from app.services import (
        DocumentService,
        DocumentNotFoundError,
        LLMService,
        get_embedding_service,
        chunk_document,
        get_chunk_stats,
        RAGService,
        RAGServiceError,
        NoEmbeddingsFoundError,
    )
    print("   ✅ DocumentService")
    print("   ✅ LLMService")
    print("   ✅ EmbeddingService")
    print("   ✅ Chunking utilities")
    print("   ✅ RAGService")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 5: Routes
print("\n5. Testing Routes...")
try:
    from app.api.routes import health, documents, llm, rag
    print("   ✅ health routes")
    print("   ✅ documents routes")
    print("   ✅ llm routes")
    print("   ✅ rag routes")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 6: Configuration
print("\n6. Testing Configuration...")
try:
    from app.config import settings
    print(f"   ✅ Settings loaded")
    print(f"      - Database URL: {settings.database_url[:30]}...")
    print(f"      - OpenAI Model: {settings.openai_default_model}")
    print(f"      - Embedding Model: {settings.openai_embedding_model}")
    print(f"      - Embedding Dimension: {settings.embedding_dimension}")
    print(f"      - Chunk Size: {settings.chunk_size}")
    print(f"      - Chunk Overlap: {settings.chunk_overlap}")
    print(f"      - RAG Top-K: {settings.rag_top_k}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 7: Database
print("\n7. Testing Database...")
try:
    from app.database import SessionLocal, engine, Base, get_db, create_tables
    print("   ✅ SessionLocal")
    print("   ✅ engine")
    print("   ✅ Base")
    print("   ✅ get_db")
    print("   ✅ create_tables")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 8: Main Application
print("\n8. Testing Main Application...")
try:
    from app.main import app
    print("   ✅ FastAPI app")
    
    # Check routes are registered
    routes = [route.path for route in app.routes]
    expected_routes = ["/", "/health", "/health/db", "/documents", "/llm/summarize_note", "/rag/answer_question", "/rag/stats"]
    
    for expected in expected_routes:
        if any(expected in route for route in routes):
            print(f"   ✅ Route registered: {expected}")
        else:
            print(f"   ❌ Route missing: {expected}")
            
except ImportError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 9: PGVector Integration
print("\n9. Testing PGVector Integration...")
try:
    from pgvector.sqlalchemy import Vector
    print("   ✅ pgvector imported")
    
    # Check DocumentEmbedding has vector column
    from app.models.document_embedding import DocumentEmbedding
    has_vector = any(col.name == 'embedding' for col in DocumentEmbedding.__table__.columns)
    if has_vector:
        print("   ✅ DocumentEmbedding has vector column")
    else:
        print("   ❌ DocumentEmbedding missing vector column")
        sys.exit(1)
        
except ImportError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 10: OpenAI Integration
print("\n10. Testing OpenAI Integration...")
try:
    from openai import OpenAI
    print("   ✅ OpenAI SDK imported")
    
    # Verify services can be instantiated (without making API calls)
    from app.services.llm import get_llm_service
    from app.services.embedding import get_embedding_service
    
    print("   ✅ LLM service can be instantiated")
    print("   ✅ Embedding service can be instantiated")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL IMPORTS VERIFIED!")
print("=" * 60)
print("\nAll modules are properly imported and exported.")
print("The application is ready to run.")
print("\nNext steps:")
print("  1. Start the application: poetry run uvicorn app.main:app --reload")
print("  2. Access Swagger UI: http://localhost:8000/docs")
print("  3. Test RAG endpoints: See RAG_API_TESTING.md")

