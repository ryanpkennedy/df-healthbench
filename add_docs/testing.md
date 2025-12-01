# Testing Documentation

Comprehensive pytest-based test suite covering all 5 project parts with 140+ automated tests.

## Quick Start

```bash
# Run all tests
cd backend
poetry run pytest

# Run fast tests only (no LLM/API calls)
poetry run pytest -m "unit or (integration and not slow)"

# Run specific part
poetry run pytest tests/test_backend_foundation.py -v
```

## Test Coverage by Project Part

### Test Structure

```
tests/
├── conftest.py                      # Shared fixtures
├── test_backend_foundation.py       # Part 1: Backend (35 tests)
├── test_crud_operations.py          # Part 1: CRUD (25 tests)
├── test_llm_integration.py          # Part 2: LLM (21 tests)
├── test_rag_pipeline.py             # Part 3: RAG (17 tests)
├── test_embedding_chunking.py       # Part 3: Embeddings (20 tests)
├── test_agent_tools.py              # Part 4: Agent unit tests (10 tests)
├── test_agent_extraction_api.py     # Part 4: Agent API (31 tests)
└── test_fhir_conversion.py          # Part 5: FHIR (20 tests)
```

### Part 1: Backend Foundation (60 tests)

- **Files:** `test_backend_foundation.py`, `test_crud_operations.py`
- **Coverage:** Database setup, health checks, document CRUD, schema validation, service layer
- **Markers:** `@pytest.mark.integration`, `@pytest.mark.api`

### Part 2: LLM Integration (21 tests)

- **File:** `test_llm_integration.py`
- **Coverage:** Singleton pattern, summarization (text & document), caching, model validation, token tracking
- **Markers:** `@pytest.mark.slow`, `@pytest.mark.integration`, `@pytest.mark.api`

### Part 3: RAG Pipeline (37 tests)

- **Files:** `test_rag_pipeline.py`, `test_embedding_chunking.py`
- **Coverage:** PGVector setup, embeddings CRUD, vector search, chunking, RAG service, API endpoints
- **Markers:** `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- **Note:** Requires PostgreSQL with pgvector

### Part 4: Agent Extraction (41 tests)

- **Files:** `test_agent_tools.py`, `test_agent_extraction_api.py`
- **Coverage:** Agent tools (mocked), structured extraction, ICD-10/RxNorm enrichment, quality validation
- **Markers:** `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`, `@pytest.mark.api`

### Part 5: FHIR Conversion (20 tests)

- **File:** `test_fhir_conversion.py`
- **Coverage:** FHIR R4 resources, coding systems (ICD-10/RxNorm/LOINC), full pipeline, validation
- **Markers:** `@pytest.mark.integration`, `@pytest.mark.e2e`, `@pytest.mark.slow`

**Total: 140+ tests across 8 test files**

## Test Categories

### By Speed

```bash
# Unit tests (fast, no external dependencies)
pytest -m unit                    # ~30 tests, <5 seconds

# Integration tests (requires DB)
pytest -m integration             # ~110 tests, varies

# Skip slow tests (no LLM/external API calls)
pytest -m "not slow"              # ~70 tests, <10 seconds
```

### By Type

```bash
# API endpoint tests
pytest -m api                     # ~50 tests

# End-to-end tests
pytest -m e2e                     # ~10 tests
```

### By Database

- **SQLite (fast):** Unit tests, CRUD, basic API endpoints
- **PostgreSQL (required):** RAG, embeddings, pgvector operations

## Running Tests

### Prerequisites

```bash
# For fast unit tests: None
# For integration tests: PostgreSQL with pgvector running
docker-compose up -d postgres

# Or use full stack
docker-compose up -d
```

### Common Commands

```bash
# All tests
pytest

# Specific file
pytest tests/test_backend_foundation.py

# Specific test class
pytest tests/test_llm_integration.py::TestLLMService

# Specific test
pytest tests/test_rag_pipeline.py::TestPGVectorSetup::test_pgvector_extension_enabled -v

# With coverage report
pytest --cov=app --cov-report=html
# View: open htmlcov/index.html

# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

## Test Organization

### Shared Fixtures (`conftest.py`)

- **Database:** `db_session` (SQLite), `postgres_db_session` (PostgreSQL)
- **API Clients:** `test_client`, `async_client`, `test_client_postgres`, `async_client_postgres`
- **Sample Data:** `sample_document`, `sample_soap_note`, `sample_extraction_data`
- **Utilities:** `clean_database`, `reset_singletons`, `mock_openai_response`

## Performance

| Test Category          | Count | Time       | Requirements            |
| ---------------------- | ----- | ---------- | ----------------------- |
| Unit tests             | ~30   | <5s        | None                    |
| Integration (no LLM)   | ~40   | ~10s       | PostgreSQL              |
| Integration (with LLM) | ~70   | ~5-10 min  | PostgreSQL + OpenAI API |
| Full suite             | 140+  | ~10-15 min | PostgreSQL + OpenAI API |

## CI/CD Ready

Tests are designed for automated pipelines:

- ✅ No manual intervention required
- ✅ Isolated database transactions (no state pollution)
- ✅ Selective execution by markers
- ✅ Clear pass/fail reporting
- ✅ Coverage reporting support

Example CI command:

```bash
# Fast feedback (unit + integration, no slow tests)
pytest -m "not slow" --cov=app --cov-report=xml
```

## Troubleshooting

**Tests won't run:**

```bash
# Ensure in backend directory
cd backend

# Install test dependencies
poetry install --with dev
```

**PostgreSQL tests fail:**

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Verify connection
psql postgresql://dfuser:dfpassword@localhost:5432/df_healthbench -c "SELECT 1"
```

**Slow tests timeout:**

```bash
# Skip slow tests during development
pytest -m "not slow"
```
