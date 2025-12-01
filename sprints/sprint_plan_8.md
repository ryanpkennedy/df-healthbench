# Sprint Plan 8: Document Summary Caching

## Objective

Add basic caching for document summaries to avoid redundant LLM API calls when summarizing the same document multiple times.

## Overview

Implement a `document_summary` table that stores cached summaries. Before calling the LLM, check if a valid cached summary exists (where the summary's `date_updated` is later than the document's `updated_at`). If valid cache exists, return it immediately; otherwise, generate new summary and store/update cache.

## Tasks

### 1. Database Model

**File:** `backend/app/models/document_summary.py` (new)

- Create SQLAlchemy model for `document_summary` table
- Fields: `id`, `document_id` (FK), `summary_text`, `model_used`, `token_usage` (JSON), `created_at`, `updated_at`
- Add foreign key constraint to `documents.id` with CASCADE delete
- Add unique constraint on `document_id`

### 2. Database Schema Updates

**File:** `backend/app/schemas/document.py`

- Add `DocumentSummaryResponse` Pydantic schema
- Add `DocumentSummaryCreate` schema
- Include fields matching database model

### 3. CRUD Operations

**File:** `backend/app/crud/document_summary.py` (new)

- `get_summary_by_document_id(db, document_id)` - retrieve cached summary
- `create_or_update_summary(db, document_id, summary_data)` - upsert summary
- `delete_summary(db, document_id)` - remove cache entry

### 4. Service Layer Logic

**File:** `backend/app/services/document.py`

- Add `get_or_generate_summary(db, document_id, model)` method
- Logic: Check cache validity (summary.updated_at > document.updated_at)
- If valid cache exists, return cached summary
- Otherwise, call LLM service, store result in cache, return summary

### 5. Update LLM Route Handler

**File:** `backend/app/api/routes/llm.py`

- Modify `summarize_document` endpoint to use new caching service
- Return cached summary when available (add `from_cache: bool` field to response)
- Ensure proper error handling maintained

### 6. Database Initialization

**File:** `backend/app/database.py`

- Import new `DocumentSummary` model
- Ensure `Base.metadata.create_all()` includes new table

**File:** `backend/app/models/__init__.py`

- Export `DocumentSummary` model

### 7. Docker Initialization

**File:** `backend/app/main.py`

- Verify startup event creates new table automatically
- No changes needed if already using `Base.metadata.create_all()`

### 8. Update Response Schema

**File:** `backend/app/schemas/llm.py`

- Add `from_cache: bool` field to `SummarizeNoteResponse`
- Default to `False` for non-cached responses

### 9. Testing

- Test cache miss: First summarization of document should call LLM
- Test cache hit: Second summarization should return cached result
- Test cache invalidation: Update document content, verify new LLM call
- Test via Swagger UI at http://localhost:8000/docs
- Verify `from_cache` field in responses

### 10. Documentation

**File:** `backend/README.md`

- Add note about summary caching under "LLM Operations" section
- Document the `from_cache` response field
- Mention cache invalidation on document updates

## Implementation Order

1. Model → Schema → CRUD → Service → Route → Testing
2. Start with smallest unit (model) and work up the stack

## Success Criteria

- ✅ `document_summary` table created automatically on startup
- ✅ First document summarization calls LLM and caches result
- ✅ Subsequent summarizations return cached result (no LLM call)
- ✅ Updating document invalidates cache, triggers new LLM call
- ✅ Response includes `from_cache` boolean field
- ✅ No breaking changes to existing API contracts

## Time Estimate

45-60 minutes total
