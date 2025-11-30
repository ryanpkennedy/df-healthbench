# Sprint Plan 2: LLM API Integration (Part 2)

**Objective:** Integrate OpenAI API to enable LLM-powered summarization of medical documents

**Total Estimated Time:** 2 hours

**Prerequisites:**

- Part 1 completed ✅
- OpenAI API key available
- Backend server running

---

## Phase 1: OpenAI Setup & Configuration (20 minutes)

### 1.1 Install OpenAI SDK

- Add `openai` package to Poetry dependencies
- Run `poetry add openai`
- Verify installation in `poetry.lock`

**Estimated time:** 3 minutes

### 1.2 Update Environment Configuration

- Add `OPENAI_API_KEY` to `.env` file
- Update `.env.example` with placeholder for `OPENAI_API_KEY`
- Update `app/config.py` to include OpenAI configuration:
  - API key from environment
  - Default model setting (e.g., `gpt-4o-mini` for cost efficiency)
  - Temperature
  - Optional: timeout settings

**Estimated time:** 7 minutes

### 1.3 Update Documentation

- Add OpenAI setup instructions to `backend/README.md`
- Document environment variable requirements
- Add example of obtaining OpenAI API key

**Estimated time:** 10 minutes

---

## Phase 2: LLM Service Layer (35 minutes)

### 2.1 Create LLM Client Wrapper

- Create `app/services/llm.py`
- Implement `LLMService` class with methods:
  - `__init__()` - Initialize OpenAI client with config
  - `_create_completion()` - Private method for making API calls
  - Error handling for API failures (rate limits, invalid key, network issues)
  - Logging for all LLM calls (prompt length, model used, response time)

**Estimated time:** 15 minutes

### 2.2 Implement Summarization Method

- Add `summarize_note(text: str)` method to `LLMService`
- Design system prompt for medical note summarization:
  - Extract key clinical information
  - Maintain medical accuracy
  - Structured output format
- Handle edge cases:
  - Empty or very short text
  - Text exceeding token limits
  - Invalid API responses
- Return structured response with:
  - Summary text
  - Model used
  - Token usage (for monitoring costs)

**Estimated time:** 20 minutes

---

## Phase 3: API Endpoint Implementation (30 minutes)

### 3.1 Create Pydantic Schemas

- Create `app/schemas/llm.py`
- Define request schema:
  - `SummarizeRequest` with `text` field (required, min length validation)
- Define response schema:
  - `SummarizeResponse` with fields:
    - `summary: str`
    - `model_used: str`
    - `token_usage: dict` (optional, for transparency)
    - `processing_time_ms: int` (optional)

**Estimated time:** 10 minutes

### 3.2 Create Summarization Route

- Create `app/api/routes/llm.py`
- Implement `POST /summarize_note` endpoint:
  - Accept `SummarizeRequest` body
  - Call `LLMService.summarize_note()`
  - Return `SummarizeResponse`
  - HTTP status codes:
    - 200: Success
    - 400: Invalid input (empty text, too long)
    - 500: LLM API error
    - 503: Service unavailable (rate limit)
- Add proper error handling with descriptive messages
- Include request/response logging

**Estimated time:** 15 minutes

### 3.3 Register Route in Main App

- Update `app/api/routes/__init__.py` to export llm router
- Update `app/main.py` to include llm routes
- Verify endpoint appears in Swagger docs

**Estimated time:** 5 minutes

---

## Phase 4: Testing & Validation (25 minutes)

### 4.1 Manual Testing

- Start server with valid OpenAI API key
- Test with curl/Postman:
  - Valid SOAP note (use one from `soap/` directory)
  - Empty text (should fail gracefully)
  - Very long text (test token limit handling)
  - Invalid API key (test error handling)
- Verify responses in Swagger UI
- Check logs for proper tracking

**Estimated time:** 15 minutes

### 4.2 Create Automated Test Script

- Create `backend/test_llm_integration.py`
- Test cases:
  - ✅ Successful summarization with valid note
  - ✅ Error handling with empty text
  - ✅ Error handling with missing API key
  - ✅ Response schema validation
  - ✅ Token usage reporting
- Use pytest with proper fixtures
- Mock OpenAI responses for tests (use `unittest.mock`)

**Estimated time:** 10 minutes

---

## Phase 5: Documentation & Polish (10 minutes)

### 5.1 Update README

- Add "LLM Integration" section to `backend/README.md`
- Document new endpoint with examples:
  - curl command
  - Expected request/response
  - Error scenarios
- Add testing instructions

**Estimated time:** 7 minutes

### 5.2 Update Project Status

- Mark Part 2 as completed in README
- Update feature checklist

**Estimated time:** 3 minutes

---

## Deliverables Checklist

- [ ] OpenAI SDK installed via Poetry
- [ ] `OPENAI_API_KEY` in environment configuration
- [ ] `app/services/llm.py` - LLM service layer
- [ ] `app/schemas/llm.py` - Request/response schemas
- [ ] `app/api/routes/llm.py` - Summarization endpoint
- [ ] `POST /summarize_note` working and documented in Swagger
- [ ] Error handling for API failures
- [ ] Logging for all LLM operations
- [ ] `test_llm_integration.py` - Automated tests
- [ ] Updated README with Part 2 documentation
- [ ] Manual testing completed successfully

---

## Success Criteria

1. ✅ `POST /summarize_note` endpoint accepts medical note text
2. ✅ Endpoint calls OpenAI API and returns summary
3. ✅ Proper error handling for all failure modes
4. ✅ No API keys in code (environment variables only)
5. ✅ Comprehensive logging for debugging
6. ✅ Token usage tracked for cost monitoring
7. ✅ Documentation updated with examples
8. ✅ Automated tests pass

---

## Stretch Goals (Optional - if time permits)

### Optional Enhancement 1: Multiple Task Types (15 minutes)

- Add `POST /extract_chief_complaint` endpoint
- Add `POST /simplify_note` endpoint (layperson terms)
- Reuse `LLMService` with different prompts

### Optional Enhancement 2: Response Caching (20 minutes)

- Add `llm_cache` table to database:
  - `text_hash` (index)
  - `prompt_type`
  - `response`
  - `created_at`
- Check cache before calling OpenAI
- Store responses for reuse
- Add cache hit/miss to response metadata

### Optional Enhancement 3: Model Selection (10 minutes)

- Add `model` parameter to request schema
- Support multiple models: `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo`
- Add model validation
- Document model options and cost implications

---

## Risk Mitigation

**Risk:** OpenAI API rate limits  
**Mitigation:** Implement exponential backoff, return 503 with retry-after header

**Risk:** High API costs during testing  
**Mitigation:** Use `gpt-4o-mini` by default, add token usage logging

**Risk:** Slow API responses  
**Mitigation:** Set reasonable timeout (30s), return error if exceeded

**Risk:** Invalid API key  
**Mitigation:** Validate key on startup, clear error messages to user

---

## Notes for Implementation

- Follow existing code patterns from Part 1 (service → route architecture)
- Use async/await for OpenAI API calls (non-blocking)
- Add comprehensive docstrings to all new functions
- Maintain consistent error response format
- Log all API calls with timing for monitoring
- Consider using `tiktoken` library for token counting before API calls
