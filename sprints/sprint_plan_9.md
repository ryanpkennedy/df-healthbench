# Sprint Plan 9: Pytest-Based Testing System Migration

**Goal:** Convert script-based tests to proper pytest format with best practices for Python projects

**Time Budget:** 1 hour

**Current State Analysis:**

- ✅ 1 file already pytest-ready: `test_agent_tools.py` (unit tests with proper structure)
- ❌ 9 files are script-based: need conversion to pytest format
- ❌ Missing `conftest.py` for shared fixtures
- ❌ No pytest markers for test categorization (unit/integration/e2e)
- ✅ pytest and pytest-asyncio already installed in pyproject.toml

---

## Test Organization by Project Parts

### Part 1 - Backend Foundation (FastAPI, Database, CRUD)

- `test_part1_complete.py` → `test_backend_foundation.py`
- `test_db_setup.py` → merge into `test_backend_foundation.py`
- `test_crud_service.py` → `test_crud_operations.py`

### Part 2 - LLM Integration

- Create new: `test_llm_integration.py`

### Part 3 - RAG Pipeline

- `test_rag_pipeline.py` → keep name, convert to pytest
- `test_embedding_chunking.py` → keep name, convert to pytest
- `test_pgvector_setup.py` → merge into `test_rag_pipeline.py`

### Part 4 - Agent Extraction

- `test_agent_tools.py` → ✅ already pytest (no changes)
- `test_agent_extraction_api.py` → keep name, convert to pytest
- `test_extraction_by_id.py` → merge into `test_agent_extraction_api.py`

### Part 5 - FHIR Conversion

- `test_fhir_conversion.py` → keep name, convert to pytest

### Cleanup

- `verify_imports.py` → keep as utility script (not a test)
- JSON test data files → keep as-is

---

## Detailed Tasks

### Task 1: Create conftest.py with Shared Fixtures (10 min)

**Deliverable:** `backend/tests/conftest.py`

**Fixtures to create:**

1. `db_session` - Database session fixture with transaction rollback
2. `test_client` - FastAPI TestClient for API endpoint tests
3. `async_client` - httpx AsyncClient for async tests
4. `sample_document` - Pre-created test document fixture
5. `sample_soap_note` - Load SOAP note from med_docs
6. `clean_database` - Fixture to ensure clean state between tests

**Benefits:**

- Eliminates code duplication across test files
- Provides consistent test setup/teardown
- Automatic database transaction rollback for test isolation

---

### Task 2: Add Pytest Markers (3 min)

**Deliverable:** Update `backend/pyproject.toml`

**Add to `[tool.pytest.ini_options]`:**

```toml
markers = [
    "unit: Unit tests (fast, no external dependencies)",
    "integration: Integration tests (requires DB and services)",
    "e2e: End-to-end tests (requires running server)",
    "api: API endpoint tests",
    "slow: Slow tests (LLM calls, external APIs)"
]
```

**Usage:**

- Unit tests: Fast, mocked, no external deps
- Integration tests: Database required, mocked external APIs (NLM, OpenAI)
- E2E tests: Full running server, real API calls

---

### Task 3: Convert Part 1 (Backend) Tests (10 min)

**Files:**

- Create `test_backend_foundation.py` (consolidate db_setup + part1_complete)
- Convert `test_crud_service.py` → `test_crud_operations.py`

**Structure:**

```python
# test_backend_foundation.py
class TestDatabaseSetup:
    def test_database_connection(self, db_session): ...
    def test_create_tables(self, db_session): ...

class TestHealthEndpoints:
    def test_health_check(self, test_client): ...
    def test_health_db(self, test_client, db_session): ...

class TestDocumentEndpoints:
    def test_list_documents(self, test_client): ...
    def test_create_document(self, test_client): ...
    def test_get_document(self, test_client, sample_document): ...
    def test_delete_document(self, test_client, sample_document): ...
```

**Markers:** `@pytest.mark.integration`, `@pytest.mark.api`

---

### Task 4: Create Part 2 (LLM) Tests (8 min)

**File:** Create `test_llm_integration.py`

**Test coverage:**

```python
class TestLLMService:
    @pytest.mark.integration
    def test_llm_service_singleton(self): ...

    @pytest.mark.slow
    @pytest.mark.integration
    def test_summarize_note(self, sample_soap_note): ...

class TestLLMEndpoints:
    @pytest.mark.api
    @pytest.mark.slow
    def test_summarize_note_endpoint(self, test_client): ...

    @pytest.mark.api
    @pytest.mark.slow
    def test_summarize_document_endpoint(self, test_client, sample_document): ...

    @pytest.mark.api
    def test_summarize_caching(self, test_client, sample_document): ...

    @pytest.mark.api
    def test_invalid_model_error(self, test_client): ...
```

**Markers:** `@pytest.mark.slow` (LLM API calls), `@pytest.mark.integration`

---

### Task 5: Convert Part 3 (RAG) Tests (10 min)

**Files:**

- Convert `test_rag_pipeline.py` (consolidate pgvector_setup)
- Convert `test_embedding_chunking.py`

**Structure:**

```python
# test_rag_pipeline.py
class TestPGVectorSetup:
    @pytest.mark.integration
    def test_vector_extension_installed(self, db_session): ...

class TestEmbeddingCRUD:
    @pytest.mark.integration
    def test_create_embedding(self, db_session, sample_document): ...

    @pytest.mark.integration
    def test_vector_similarity_search(self, db_session): ...

class TestRAGService:
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_embed_document(self, db_session, sample_document): ...

    @pytest.mark.integration
    @pytest.mark.slow
    async def test_answer_question(self, db_session): ...

class TestRAGEndpoints:
    @pytest.mark.api
    def test_rag_stats(self, test_client): ...

    @pytest.mark.api
    @pytest.mark.slow
    async def test_answer_question_endpoint(self, async_client): ...

# test_embedding_chunking.py
class TestChunkingService:
    @pytest.mark.unit
    def test_chunk_document(self): ...

    @pytest.mark.unit
    def test_chunk_stats(self): ...

    @pytest.mark.unit
    def test_soap_aware_chunking(self, sample_soap_note): ...

class TestEmbeddingService:
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_generate_single_embedding(self): ...

    @pytest.mark.integration
    @pytest.mark.slow
    async def test_batch_embedding_generation(self): ...
```

**Markers:** Mix of `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`

---

### Task 6: Convert Part 4 (Agent) Integration Tests (8 min)

**Files:**

- Keep `test_agent_tools.py` as-is (already pytest ✅)
- Convert `test_agent_extraction_api.py` (consolidate extraction_by_id)

**Structure:**

```python
# test_agent_extraction_api.py
class TestAgentExtractionService:
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_extract_structured_data(self, sample_soap_note): ...

    @pytest.mark.integration
    def test_icd10_enrichment(self): ...  # mocked APIs

    @pytest.mark.integration
    def test_rxnorm_enrichment(self): ...  # mocked APIs

class TestAgentExtractionEndpoints:
    @pytest.mark.api
    @pytest.mark.slow
    async def test_extract_structured_endpoint(self, async_client, sample_soap_note): ...

    @pytest.mark.api
    @pytest.mark.slow
    async def test_extract_by_document_id(self, async_client, sample_document): ...

    @pytest.mark.api
    async def test_extraction_error_handling(self, async_client): ...
```

**Note:** test_agent_tools.py already has proper unit tests with mocked APIs ✅

**Markers:** `@pytest.mark.integration`, `@pytest.mark.slow`, `@pytest.mark.api`

---

### Task 7: Convert Part 5 (FHIR) Tests (8 min)

**File:** Convert `test_fhir_conversion.py`

**Structure:**

```python
# test_fhir_conversion.py
class TestFHIRConversionService:
    @pytest.mark.integration
    def test_convert_patient_resource(self): ...

    @pytest.mark.integration
    def test_convert_condition_resource(self): ...

    @pytest.mark.integration
    def test_convert_medication_resource(self): ...

    @pytest.mark.integration
    def test_convert_observation_resource(self): ...

class TestFHIREndpoints:
    @pytest.mark.api
    def test_fhir_health(self, test_client): ...

    @pytest.mark.api
    @pytest.mark.e2e
    def test_fhir_convert_endpoint(self, test_client): ...

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_full_pipeline_soap_to_fhir(self, test_client, sample_soap_note): ...
```

**Markers:** `@pytest.mark.integration`, `@pytest.mark.e2e`, `@pytest.mark.api`

---

### Task 8: Update Testing Documentation (3 min)

**File:** Update `backend/tests/README_TESTS.md`

**New sections:**

1. Quick Start (run all tests)
2. Run by category (unit/integration/e2e)
3. Run by project part (Part 1-5)
4. Run specific tests
5. Coverage reporting
6. CI/CD recommendations

**Example commands:**

```bash
# Run all tests
pytest

# Run only fast unit tests
pytest -m unit

# Run integration tests (DB required)
pytest -m integration

# Run without slow tests (no LLM calls)
pytest -m "not slow"

# Run specific part
pytest tests/test_backend_foundation.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_llm_integration.py::TestLLMService::test_summarize_note -v
```

---

## Expected Outcomes

### Before (Current State):

- 9 script-based test files that must be run individually
- Manual tracking of pass/fail with print statements
- No shared fixtures (code duplication)
- No test categorization
- Difficult to run selectively
- No coverage reporting

### After (Pytest System):

```bash
# Single command to run all tests
$ pytest

# Output:
tests/test_backend_foundation.py ................ [ 15%]
tests/test_llm_integration.py ............ [ 30%]
tests/test_rag_pipeline.py ................. [ 50%]
tests/test_embedding_chunking.py ......... [ 65%]
tests/test_agent_tools.py ................... [ 75%]
tests/test_agent_extraction_api.py ....... [ 85%]
tests/test_fhir_conversion.py ........... [100%]

========== 87 passed, 3 skipped in 45.23s ==========
```

### Benefits:

- ✅ Single command to run all tests (`pytest`)
- ✅ Proper pass/fail reporting with counts
- ✅ Shared fixtures eliminate duplication
- ✅ Test categorization with markers
- ✅ Selective test execution (unit/integration/e2e)
- ✅ Coverage reporting available
- ✅ CI/CD ready
- ✅ Standard Python testing practices
- ✅ Clear test organization by project part

---

## Test File Summary

### Files to CREATE:

1. `conftest.py` - Shared fixtures
2. `test_backend_foundation.py` - Consolidates db_setup + part1_complete
3. `test_llm_integration.py` - New LLM-specific tests

### Files to CONVERT (keep name):

4. `test_crud_operations.py` - Rename from test_crud_service.py
5. `test_rag_pipeline.py` - Convert to pytest + consolidate pgvector_setup
6. `test_embedding_chunking.py` - Convert to pytest
7. `test_agent_extraction_api.py` - Convert to pytest + consolidate extraction_by_id
8. `test_fhir_conversion.py` - Convert to pytest

### Files to KEEP AS-IS:

9. `test_agent_tools.py` - ✅ Already proper pytest format

### Files to DELETE (consolidated or obsolete):

10. `test_part1_complete.py` - Consolidated into test_backend_foundation.py
11. `test_db_setup.py` - Consolidated into test_backend_foundation.py
12. `test_crud_service.py` - Renamed to test_crud_operations.py
13. `test_pgvector_setup.py` - Consolidated into test_rag_pipeline.py
14. `test_extraction_by_id.py` - Consolidated into test_agent_extraction_api.py

### Files to KEEP (utilities/docs):

15. `verify_imports.py` - Utility script, not a test
16. `README_TESTS.md` - Update with new structure
17. `RAG_API_TESTING.md` - Keep for RAG documentation
18. `*.json` - Test data files

---

## Execution Order

1. ✅ **Task 1:** Create conftest.py (10 min)
2. ✅ **Task 2:** Add pytest markers (3 min)
3. ✅ **Task 3:** Convert Part 1 tests (10 min)
4. ✅ **Task 4:** Create Part 2 tests (8 min)
5. ✅ **Task 5:** Convert Part 3 tests (10 min)
6. ✅ **Task 6:** Convert Part 4 integration tests (8 min)
7. ✅ **Task 7:** Convert Part 5 tests (8 min)
8. ✅ **Task 8:** Update documentation (3 min)
9. ✅ **Cleanup:** Delete obsolete test files (1 min)
10. ✅ **Validation:** Run full pytest suite and verify all pass (1 min)

**Total Time:** ~62 minutes (within 1 hour budget with small buffer)

---

## Success Criteria

- [ ] All tests converted to pytest format
- [ ] Can run `pytest` once and get comprehensive results
- [ ] Tests properly marked with unit/integration/e2e markers
- [ ] Shared fixtures in conftest.py eliminate duplication
- [ ] Coverage for all 5 project parts (Backend, LLM, RAG, Agent, FHIR)
- [ ] Clear documentation of how to run tests
- [ ] Obsolete script-based tests cleaned up
- [ ] All tests pass with proper pytest output

---

## Risk Mitigation

**Risk:** Tests fail after conversion
**Mitigation:** Convert one part at a time, validate before moving to next

**Risk:** Time overrun (>1 hour)
**Mitigation:** Priority order: conftest.py → Part 1 → Part 4 → Part 5 → Part 3 → Part 2

**Risk:** Complex async tests
**Mitigation:** pytest-asyncio already configured in pyproject.toml with `asyncio_mode = "auto"`

**Risk:** Database state issues between tests
**Mitigation:** Use transaction-based fixtures with rollback in conftest.py

---

## Post-Sprint Actions (Future)

- Add pytest-cov configuration for coverage thresholds
- Add pytest-xdist for parallel test execution
- Create GitHub Actions workflow for CI/CD
- Add pytest-mock for easier mocking
- Consider pytest-timeout for slow test limits
