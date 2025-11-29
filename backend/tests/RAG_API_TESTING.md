# RAG API Testing Guide

Quick reference for testing the RAG endpoints.

## Prerequisites

1. **Start the application:**
   ```bash
   cd backend
   poetry run uvicorn app.main:app --reload
   ```

2. **Access Swagger UI:**
   - Open browser: http://localhost:8000/docs
   - All RAG endpoints are under the "RAG" tag

## API Endpoints

### 1. GET /rag/stats

**Purpose:** Check RAG system status and statistics

**Example Request:**
```bash
curl http://localhost:8000/rag/stats
```

**Expected Response:**
```json
{
  "total_documents": 7,
  "total_embeddings": 0,
  "documents_with_embeddings": 0,
  "avg_chunks_per_document": 0,
  "embedding_dimension": 1536,
  "embedding_model": "text-embedding-3-small",
  "chunk_size": 800,
  "chunk_overlap": 50,
  "rag_top_k": 3
}
```

---

### 2. POST /rag/embed_all

**Purpose:** Embed all documents in the database

**Example Request (via Swagger):**
- Click "Try it out"
- Leave `force` as `false` (default)
- Click "Execute"

**Example Request (via curl):**
```bash
curl -X POST "http://localhost:8000/rag/embed_all?force=false"
```

**Expected Response:**
```json
{
  "documents_processed": 7,
  "documents_skipped": 0,
  "total_chunks": 45,
  "total_embeddings": 45,
  "processing_time_ms": 8500,
  "results": [
    {
      "document_id": 1,
      "document_title": "SOAP Note - Soap 01",
      "chunks_created": 6,
      "embeddings_created": 6,
      "skipped": false,
      "error": null
    },
    ...
  ]
}
```

**Note:** This will take 30-60 seconds depending on the number of documents.

---

### 3. POST /rag/embed_document/{document_id}

**Purpose:** Embed a single document

**Example Request (via Swagger):**
- Click "Try it out"
- Enter document ID: `1`
- Leave `force` as `false`
- Click "Execute"

**Example Request (via curl):**
```bash
curl -X POST "http://localhost:8000/rag/embed_document/1?force=false"
```

**Expected Response:**
```json
{
  "document_id": 1,
  "document_title": "SOAP Note - Soap 01",
  "chunks_created": 6,
  "embeddings_created": 6,
  "processing_time_ms": 1500,
  "skipped": false
}
```

---

### 4. POST /rag/answer_question

**Purpose:** Answer a question using the RAG pipeline

**⚠️ Important:** Documents must be embedded first (use `/rag/embed_all`)

**Example Request (via Swagger):**
- Click "Try it out"
- Enter request body:
  ```json
  {
    "question": "What medications are mentioned in the notes?",
    "top_k": 3
  }
  ```
- Click "Execute"

**Example Request (via curl):**
```bash
curl -X POST "http://localhost:8000/rag/answer_question" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What medications are mentioned in the notes?",
    "top_k": 3
  }'
```

**Expected Response:**
```json
{
  "answer": "Based on the medical documents, several medications are mentioned:\n\n1. According to Source 1, metformin is prescribed for diabetes management...",
  "sources": [
    {
      "document_id": 3,
      "document_title": "SOAP Note - Soap 03",
      "chunk_index": 2,
      "chunk_text": "A:\n\nType 2 Diabetes Mellitus, poorly controlled...",
      "similarity_score": 0.8234
    },
    ...
  ],
  "model_used": "gpt-5-nano-2025-08-07",
  "token_usage": {
    "prompt_tokens": 450,
    "completion_tokens": 120,
    "total_tokens": 570
  },
  "processing_time_ms": 2100,
  "retrieval_time_ms": 150,
  "generation_time_ms": 1950
}
```

---

## Sample Questions to Test

Try these questions after embedding documents:

1. **Medications:**
   ```json
   {"question": "What medications are mentioned in the notes?"}
   ```

2. **Vital Signs:**
   ```json
   {"question": "What are the patient's vital signs?"}
   ```

3. **Follow-up Care:**
   ```json
   {"question": "What follow-up appointments were scheduled?"}
   ```

4. **Diagnoses:**
   ```json
   {"question": "What diagnoses are documented?"}
   ```

5. **Lab Results:**
   ```json
   {"question": "What lab tests were ordered?"}
   ```

---

## Testing Workflow

### First-Time Setup:

1. **Check initial stats:**
   ```bash
   curl http://localhost:8000/rag/stats
   ```
   - Should show `total_embeddings: 0`

2. **Embed all documents:**
   ```bash
   curl -X POST "http://localhost:8000/rag/embed_all"
   ```
   - Wait 30-60 seconds
   - Should process all 7 documents

3. **Verify embeddings created:**
   ```bash
   curl http://localhost:8000/rag/stats
   ```
   - Should show `total_embeddings: 40-50` (depending on chunking)

4. **Ask a question:**
   ```bash
   curl -X POST "http://localhost:8000/rag/answer_question" \
     -H "Content-Type: application/json" \
     -d '{"question": "What medications are mentioned?"}'
   ```
   - Should return answer with sources

---

## Troubleshooting

### Error: "No document embeddings found"

**Solution:** Run `/rag/embed_all` first to create embeddings.

### Error: "Document with ID X not found"

**Solution:** Check available document IDs with `GET /documents`.

### Slow response times

**Normal behavior:**
- First embedding: ~5-10 seconds per document (OpenAI API calls)
- Question answering: ~2-3 seconds (retrieval + LLM generation)

### No relevant sources found

**Solutions:**
- Try a more specific question
- Adjust `similarity_threshold` (lower = more permissive)
- Increase `top_k` to retrieve more chunks

---

## Advanced Options

### Similarity Threshold

Control minimum similarity for retrieved chunks:

```json
{
  "question": "What medications?",
  "similarity_threshold": 0.7
}
```

- Range: 0.0 to 1.0
- Higher = more strict (only very similar chunks)
- Lower = more permissive (includes less similar chunks)

### Top-K

Control number of chunks to retrieve:

```json
{
  "question": "What medications?",
  "top_k": 5
}
```

- Default: 3 (from config)
- Range: 1 to 10
- More chunks = more context but higher token cost

### Model Override

Use a different LLM model:

```json
{
  "question": "What medications?",
  "model": "gpt-5-mini"
}
```

Available models:
- `gpt-5-nano` (default, fastest, cheapest)
- `gpt-5-mini` (balanced)
- `gpt-5` (highest quality)

---

## Performance Metrics

Each response includes timing metrics:

- `processing_time_ms`: Total time (retrieval + generation)
- `retrieval_time_ms`: Time for vector search
- `generation_time_ms`: Time for LLM answer generation

**Typical values:**
- Retrieval: 50-200ms
- Generation: 1000-3000ms
- Total: 1500-3500ms

---

## Next Steps

After testing the RAG endpoints:

1. Test with different question types
2. Experiment with `top_k` and `similarity_threshold`
3. Try different LLM models
4. Check source citations for accuracy
5. Monitor token usage for cost tracking

