# Testing Guide

## Running Tests

### Unit Tests (Agent Tools)

Test individual agent tools with mocked external APIs:

```bash
cd backend

# Install test dependencies first (if needed)
poetry install --with dev

# Run agent tool unit tests
poetry run pytest tests/test_agent_tools.py -v

# Run with detailed output
poetry run pytest tests/test_agent_tools.py -v -s

# Run specific test class
poetry run pytest tests/test_agent_tools.py::TestICD10Lookup -v

# Run specific test method
poetry run pytest tests/test_agent_tools.py::TestICD10Lookup::test_icd10_exact_match -v
```

### Integration Tests (API Endpoints)

Test full API endpoints (requires server running):

```bash
# Start the server first
docker-compose up -d
# OR
poetry run uvicorn app.main:app --reload

# Run integration tests
poetry run python tests/test_agent_extraction_api.py
poetry run python tests/test_fhir_conversion.py
poetry run python tests/test_rag_pipeline.py
```

## Test Categories

### Unit Tests (Mocked)
- `test_agent_tools.py` - Agent tool functions with mocked APIs
- No server required
- No external API calls
- Fast execution (~1-2 seconds)

### Integration Tests (Live API)
- `test_agent_extraction_api.py` - Full agent extraction pipeline
- `test_fhir_conversion.py` - Extraction + FHIR conversion
- `test_rag_pipeline.py` - RAG question answering
- Requires server running
- Makes real OpenAI API calls
- Slower execution (30-60 seconds per test)

## Test Coverage

### Agent Tools (Unit Tests)
✅ ICD-10-CM lookup with exact match  
✅ ICD-10-CM lookup with no results  
✅ ICD-10-CM lookup with API errors  
✅ ICD-10-CM lookup with empty string  
✅ ICD-10-CM lookup with multiple results  
✅ RxNorm lookup with exact match  
✅ RxNorm lookup with approximate match  
✅ RxNorm lookup with no results  
✅ RxNorm lookup with API errors  
✅ RxNorm lookup with empty string  

## Benefits of Unit Tests

- **Fast**: No network calls, instant feedback
- **Reliable**: Not affected by external API availability
- **Comprehensive**: Test edge cases and error handling
- **No cost**: No OpenAI API credits used
- **CI/CD friendly**: Can run in automated pipelines

## Notes

- Unit tests use `unittest.mock` to mock httpx.AsyncClient
- Integration tests require `OPENAI_API_KEY` in environment
- All tests are non-destructive (read-only operations)

