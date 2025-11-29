# Sprint Plan 3: RAG Pipeline Implementation

**Estimated Time:** 2 hours  
**Goal:** Implement a production-ready RAG pipeline using PGVector for semantic search over medical documents

---

## Overview

This sprint implements Part 3 of the project: a Retrieval-Augmented Generation (RAG) pipeline that enables semantic search and question-answering over the medical document knowledge base.

**Key Technologies:**

- **PGVector**: PostgreSQL extension for vector similarity search
- **OpenAI Embeddings**: `text-embedding-3-small` (efficient, cost-effective)
- **Existing Stack**: FastAPI, SQLAlchemy, PostgreSQL

**Architecture Decision:**

- Use PGVector extension in existing PostgreSQL database (no separate vector DB needed)
- Store embeddings in a new `document_embeddings` table with vector column
- Chunk documents into semantic sections for better retrieval
- Leverage existing LLM service singleton pattern

---

## Task Breakdown

### 1. Database & Infrastructure Setup (20 minutes)

#### 1.1 Update Docker Compose for PGVector

- **File:** `docker-compose.yml`
- **Changes:**
  - Switch from `postgres:15-alpine` to `pgvector/pgvector:pg15` image
  - Add initialization script volume mount for enabling extension
  - Keep existing environment variables and ports

#### 1.2 Create Database Migration

- **File:** `backend/app/models/document_embedding.py` (new)
- **Changes:**
  - Create `DocumentEmbedding` SQLAlchemy model
  - Fields: `id`, `document_id` (FK), `chunk_index`, `chunk_text`, `embedding` (vector), `created_at`
  - Add relationship to `Document` model

#### 1.3 Database Initialization Script

- **File:** `backend/init_pgvector.sql` (new)
- **Changes:**
  - SQL script to enable `pgvector` extension
  - Create vector index for fast similarity search

#### 1.4 Update Database Module

- **File:** `backend/app/database.py`
- **Changes:**
  - Import new `DocumentEmbedding` model in `create_tables()`
  - No other changes needed (existing connection pooling works)

---

### 2. Embedding Service Layer (25 minutes)

#### 2.1 Create Embedding Service

- **File:** `backend/app/services/embedding.py` (new)
- **Purpose:** Handle OpenAI embedding generation
- **Key Methods:**
  - `generate_embedding(text: str) -> List[float]` - Generate single embedding
  - `generate_embeddings_batch(texts: List[str]) -> List[List[float]]` - Batch processing
- **Features:**
  - Use OpenAI `text-embedding-3-small` (1536 dimensions, $0.02/1M tokens)
  - Singleton pattern (reuse OpenAI client)
  - Error handling (rate limits, timeouts)
  - Batch processing for efficiency (up to 100 texts per request)

#### 2.2 Create Document Chunking Utility

- **File:** `backend/app/services/chunking.py` (new)
- **Purpose:** Split documents into semantic chunks
- **Key Function:**
  - `chunk_document(content: str) -> List[str]` - Split by sections/paragraphs
- **Strategy:**
  - Split on double newlines (paragraphs)
  - Target chunk size: 500-800 characters
  - Preserve SOAP note structure (S/O/A/P sections)
  - Add overlap between chunks (50 chars) for context

---

### 3. CRUD & Service Layer for Embeddings (20 minutes)

#### 3.1 Embedding CRUD Operations

- **File:** `backend/app/crud/embedding.py` (new)
- **Functions:**
  - `create_embedding(db, document_id, chunk_index, chunk_text, embedding)` - Store embedding
  - `get_embeddings_by_document(db, document_id)` - Get all chunks for a document
  - `search_similar_chunks(db, query_embedding, limit=5)` - Vector similarity search
  - `delete_embeddings_by_document(db, document_id)` - Clean up embeddings
  - `count_embeddings(db)` - Get total embedding count

#### 3.2 RAG Service Layer

- **File:** `backend/app/services/rag.py` (new)
- **Purpose:** High-level RAG orchestration
- **Key Methods:**
  - `embed_document(document_id)` - Chunk and embed a document
  - `embed_all_documents()` - Process all documents in DB
  - `answer_question(question, top_k=3)` - RAG query pipeline
- **RAG Pipeline Logic:**
  1. Generate embedding for user question
  2. Search for top-k similar chunks using cosine similarity
  3. Build context from retrieved chunks
  4. Call LLM with context + question
  5. Return answer with source citations

---

### 4. API Endpoints (25 minutes)

#### 4.1 Create RAG Router

- **File:** `backend/app/api/routes/rag.py` (new)
- **Endpoints:**

**POST /rag/embed_document/{document_id}**

- Embed a specific document (chunk + generate embeddings)
- Response: `{"document_id": 1, "chunks_created": 8, "processing_time_ms": 1500}`

**POST /rag/embed_all**

- Embed all documents in database
- Response: `{"documents_processed": 6, "total_chunks": 45, "processing_time_ms": 8500}`

**POST /rag/answer_question**

- Main RAG endpoint - answer questions using document knowledge base
- Request: `{"question": "What medications are mentioned for diabetes?"}`
- Response:
  ```json
  {
    "answer": "Based on the documents, metformin is mentioned...",
    "sources": [
      {"document_id": 1, "document_title": "SOAP Note 01", "chunk_text": "..."},
      {"document_id": 3, "document_title": "SOAP Note 03", "chunk_text": "..."}
    ],
    "model_used": "gpt-5-nano",
    "token_usage": {...},
    "processing_time_ms": 2100
  }
  ```

**GET /rag/stats**

- Get embedding statistics
- Response: `{"total_documents": 6, "total_chunks": 45, "embedding_dimension": 1536}`

#### 4.2 Pydantic Schemas

- **File:** `backend/app/schemas/rag.py` (new)
- **Schemas:**
  - `QuestionRequest` - Question input
  - `SourceChunk` - Retrieved chunk with metadata
  - `AnswerResponse` - Answer with sources and metadata
  - `EmbedDocumentResponse` - Embedding operation result
  - `RAGStatsResponse` - Statistics response

#### 4.3 Register Router

- **File:** `backend/app/main.py`
- **Changes:**
  - Import `rag` router
  - Add `app.include_router(rag.router, prefix="/rag", tags=["RAG"])`

---

### 5. Configuration & Dependencies (10 minutes)

#### 5.1 Update Configuration

- **File:** `backend/app/config.py`
- **Add Settings:**
  - `openai_embedding_model: str = "text-embedding-3-small"`
  - `embedding_dimension: int = 1536`
  - `chunk_size: int = 800`
  - `chunk_overlap: int = 50`
  - `rag_top_k: int = 3`

#### 5.2 Update Dependencies

- **File:** `backend/pyproject.toml`
- **Add:**
  - `pgvector = "^0.3.6"` - PGVector SQLAlchemy support

#### 5.3 Update Package Imports

- **File:** `backend/app/crud/__init__.py` - Export `embedding`
- **File:** `backend/app/services/__init__.py` - Export `rag`, `embedding`, `chunking`
- **File:** `backend/app/api/routes/__init__.py` - Export `rag`

---

### 6. Startup Seeding & Testing (20 minutes)

#### 6.1 Update Seed Script

- **File:** `backend/app/seed.py`
- **Changes:**
  - After seeding documents, automatically embed them
  - Add `--skip-embeddings` flag to skip embedding generation
  - Log embedding progress

#### 6.2 Update Startup Lifespan

- **File:** `backend/app/main.py`
- **Changes:**
  - After seeding documents, check if embeddings exist
  - If no embeddings, generate them automatically (only on first run)
  - Log embedding statistics

#### 6.3 Manual Testing Checklist

- Restart database with PGVector image
- Start application (should auto-seed and embed)
- Test `GET /rag/stats` - verify embeddings created
- Test `POST /rag/answer_question` with sample questions:
  - "What medications are mentioned in the notes?"
  - "What are the patient's vital signs?"
  - "What follow-up appointments were scheduled?"
- Verify sources are returned with answers
- Check Swagger docs at `/docs` for new endpoints

---

### 7. Documentation Updates (10 minutes)

#### 7.1 Update README

- **File:** `backend/README.md`
- **Sections to Add:**
  - RAG Pipeline overview in Architecture section
  - PGVector setup instructions
  - RAG endpoint documentation with examples
  - Update "Project Status" to mark Part 3 complete

#### 7.2 Add Inline Documentation

- Ensure all new functions have docstrings
- Add comments for complex vector operations
- Document embedding model choice and rationale

---

## Implementation Order

**Recommended sequence for efficiency:**

1. **Infrastructure First** (Tasks 1.1-1.4)

   - Update docker-compose.yml
   - Create init script
   - Restart database
   - Verify PGVector extension enabled

2. **Data Layer** (Tasks 2.1-2.2, 3.1)

   - Create models and CRUD operations
   - Test database operations manually

3. **Service Layer** (Tasks 3.2, 2.1-2.2)

   - Implement embedding service
   - Implement chunking utility
   - Implement RAG service
   - Test embedding generation

4. **API Layer** (Tasks 4.1-4.3)

   - Create schemas
   - Create endpoints
   - Register router
   - Test via Swagger UI

5. **Configuration & Polish** (Tasks 5.1-5.3, 6.1-6.2)

   - Update config
   - Update dependencies
   - Update seeding
   - Test end-to-end

6. **Documentation** (Task 7.1-7.2)
   - Update README
   - Add docstrings

---

## Success Criteria

- [ ] PGVector extension enabled in PostgreSQL
- [ ] `document_embeddings` table created with vector column
- [ ] All 6 SOAP notes chunked and embedded automatically on startup
- [ ] `POST /rag/answer_question` returns relevant answers with source citations
- [ ] Embeddings persist across application restarts
- [ ] No performance degradation (embedding generation is async/background)
- [ ] All endpoints documented in Swagger UI
- [ ] README updated with RAG setup and usage instructions

---

## Time Allocation Summary

| Phase                | Time        |
| -------------------- | ----------- |
| Database Setup       | 20 min      |
| Embedding Service    | 25 min      |
| CRUD & RAG Service   | 20 min      |
| API Endpoints        | 25 min      |
| Configuration        | 10 min      |
| Seeding & Testing    | 20 min      |
| Documentation        | 10 min      |
| **Buffer/Debugging** | **10 min**  |
| **Total**            | **2 hours** |

---

## Key Design Decisions

### Why PGVector?

- ✅ No additional infrastructure (uses existing PostgreSQL)
- ✅ ACID transactions for embeddings + documents
- ✅ Mature, production-ready extension
- ✅ Excellent performance for <100k vectors
- ✅ Simplified deployment (one database)

### Why text-embedding-3-small?

- ✅ Cost-effective ($0.02/1M tokens vs $0.13 for ada-002)
- ✅ Fast inference (lower latency)
- ✅ Sufficient quality for medical document retrieval
- ✅ 1536 dimensions (good balance of size/performance)

### Why Chunk Documents?

- ✅ Better retrieval precision (match specific sections)
- ✅ Avoid token limits in LLM context window
- ✅ Enable source citations at chunk level
- ✅ Improve semantic similarity matching

### Why Singleton Pattern for Embedding Service?

- ✅ Reuse OpenAI client (connection pooling)
- ✅ Consistent with existing LLM service pattern
- ✅ Thread-safe for concurrent requests
- ✅ Reduces initialization overhead

---

## Potential Challenges & Mitigations

| Challenge                                | Mitigation                                             |
| ---------------------------------------- | ------------------------------------------------------ |
| Docker image change breaks existing data | Use named volume (already configured), data persists   |
| Embedding generation is slow on startup  | Make it async/background, add progress logging         |
| PGVector extension not available         | Use official `pgvector/pgvector` image (pre-installed) |
| Chunk size too small/large               | Start with 800 chars, tune based on testing            |
| Vector search returns irrelevant results | Adjust top_k, add re-ranking, tune chunk strategy      |
| OpenAI rate limits during bulk embedding | Add retry logic, use batch API, add delays             |

---

## Testing Strategy

### Unit Tests (Optional - if time permits)

- `test_chunking.py` - Test document chunking logic
- `test_embedding_service.py` - Test embedding generation (mock OpenAI)
- `test_rag_service.py` - Test RAG pipeline logic

### Manual Testing (Required)

1. **Database Setup:**

   - Verify PGVector extension: `SELECT * FROM pg_extension WHERE extname = 'vector';`
   - Verify table created: `\d document_embeddings`

2. **Embedding Generation:**

   - Test single document: `POST /rag/embed_document/1`
   - Test all documents: `POST /rag/embed_all`
   - Verify stats: `GET /rag/stats`

3. **RAG Query:**

   - Ask medical questions via `POST /rag/answer_question`
   - Verify answers are relevant and cite sources
   - Test edge cases (no results, ambiguous questions)

4. **Performance:**
   - Check response times (should be <3s for typical queries)
   - Verify no memory leaks during bulk embedding

---

## Next Steps (Post-Sprint)

After completing this sprint, the following enhancements could be added:

- **Hybrid Search:** Combine vector search with keyword search (BM25)
- **Re-ranking:** Use cross-encoder model to re-rank retrieved chunks
- **Caching:** Cache embeddings for frequently asked questions
- **Streaming:** Stream LLM responses for better UX
- **Metadata Filtering:** Filter by document type, date, patient ID
- **Evaluation:** Add RAGAS metrics to measure RAG quality

---

## Notes

- All code should follow existing patterns (service layer, CRUD, schemas)
- Maintain consistent error handling (use existing exception classes)
- Log all important operations (embedding generation, vector search)
- Keep configuration in `.env` file (no hardcoded values)
- Use type hints throughout (Python 3.11+ syntax)
- Follow PEP 8 style guide
