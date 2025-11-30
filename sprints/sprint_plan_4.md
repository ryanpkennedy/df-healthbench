# Sprint Plan 4: Agent for Structured Data Extraction

**Estimated Time:** 2 hours  
**Goal:** Build an agentic system that extracts structured clinical data from medical notes and enriches it with ICD-10-CM and RxNorm codes

---

## Overview

This sprint implements Part 4 of the project: an agent-based workflow using OpenAI Agents SDK to:

1. Extract clinical entities from unstructured SOAP notes (conditions, medications, vitals, etc.)
2. Enrich diagnoses with ICD-10-CM codes via NLM Clinical Tables API
3. Enrich medications with RxNorm codes via NLM RxNav API
4. Return validated, structured data as Pydantic models

**Key Technologies:**

- **OpenAI Agents SDK**: Multi-agent framework with function tools
- **NLM Clinical Tables API**: Free ICD-10-CM code lookup
- **NLM RxNav API**: Free RxNorm medication code lookup
- **Jupyter Notebook**: Rapid prototyping and testing
- **Pydantic**: Structured data validation

**Architecture Approach:**

1. **Prototype in Notebook** (Phase 1-3): Develop and test agent + tools interactively
2. **Integrate into Backend** (Phase 4-5): Convert notebook code to service layer + API endpoint

---

## Phase 1: Setup & Dependencies (10 minutes)

### 1.1 Install OpenAI Agents SDK

- Add to Poetry dependencies: `poetry add "openai-agents-python" httpx`
- Verify installation in notebook
- **Estimated time:** 3 minutes

### 1.2 Create Jupyter Notebook

- Create `backend/notebooks/agent_extraction_prototype.ipynb`
- Add folder to `.gitignore` if needed: `notebooks/*.ipynb` (keep in repo for now)
- Set up notebook sections:
  - Section 1: Imports and configuration
  - Section 2: Define function tools
  - Section 3: Define Pydantic schemas
  - Section 4: Create agent
  - Section 5: Test with SOAP notes
- **Estimated time:** 5 minutes

### 1.3 Test API Access

- Test NLM Clinical Tables API call (ICD-10-CM search)
- Test NLM RxNav API call (RxNorm lookup)
- Verify no auth required, responses are JSON
- **Estimated time:** 2 minutes

---

## Phase 2: Define Function Tools (Notebook) (30 minutes)

### 2.1 Tool 1: Extract Clinical Entities

**Purpose:** Use LLM to extract raw clinical data from SOAP note

**Implementation in notebook:**

```python
from agents import function_tool
from typing import List

@function_tool
def extract_clinical_entities(note_text: str) -> dict:
    """
    Extract clinical entities from medical note using LLM.
    Returns dict with: diagnoses, medications, vital_signs, lab_results,
    plan_actions, patient_info
    """
    # Use OpenAI client to call GPT with structured extraction prompt
    # System prompt: extract conditions, meds, vitals, labs, plans
    # Return JSON dict
```

**Key Details:**

- Use structured output (JSON mode or function calling)
- Extract: diagnoses (list), medications (list), vital_signs (dict), lab_results (list), plan_actions (list)
- Keep it simple - extract text as-is, don't try to normalize yet

**Estimated time:** 12 minutes

---

### 2.2 Tool 2: Lookup ICD-10-CM Codes

**Purpose:** Convert diagnosis/condition text to ICD-10-CM codes

**Implementation in notebook:**

```python
import httpx

@function_tool
def lookup_icd10_code(condition: str) -> dict:
    """
    Look up ICD-10-CM code for a condition using NLM Clinical Tables API.
    Returns best match with code and description.
    """
    # Call: https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search?sf=code,name&terms={condition}
    # Parse response: [count, [codes], null, [names]]
    # Return: {"code": "E11.9", "name": "Type 2 diabetes mellitus...", "confidence": "high"}
```

**Key Details:**

- Use `httpx` for async HTTP requests
- Handle no results found (return empty or "unspecified" code)
- Return top result only (best match)
- Add basic error handling for API failures

**Estimated time:** 10 minutes

---

### 2.3 Tool 3: Lookup RxNorm Codes

**Purpose:** Convert medication text to RxNorm codes

**Implementation in notebook:**

```python
@function_tool
def lookup_rxnorm_code(medication: str) -> dict:
    """
    Look up RxNorm code (RxCUI) for a medication using NLM RxNav API.
    Returns RxCUI and normalized name.
    """
    # Try exact match first: https://rxnav.nlm.nih.gov/REST/rxcui.json?name={medication}
    # If not found, try approximate: https://rxnav.nlm.nih.gov/REST/approximateTerm.json?term={medication}
    # Return: {"rxcui": "860975", "name": "Metformin 500 MG Oral Tablet", "confidence": "exact"}
```

**Key Details:**

- Try exact match first (`/rxcui.json`), fall back to approximate (`/approximateTerm.json`)
- Handle medication dosages and brand names
- Return top result with confidence level
- Handle API errors gracefully

**Estimated time:** 8 minutes

---

## Phase 3: Build Agent Workflow (Notebook) (25 minutes)

### 3.1 Define Pydantic Schemas for Structured Output

**Create schemas for final structured data:**

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class VitalSigns(BaseModel):
    temperature: Optional[str] = None
    blood_pressure: Optional[str] = None
    heart_rate: Optional[str] = None
    respiratory_rate: Optional[str] = None
    oxygen_saturation: Optional[str] = None

class DiagnosisCode(BaseModel):
    text: str = Field(description="Original diagnosis text from note")
    icd10_code: Optional[str] = Field(None, description="ICD-10-CM code")
    icd10_description: Optional[str] = None
    confidence: Optional[str] = None

class MedicationCode(BaseModel):
    text: str = Field(description="Original medication text from note")
    rxnorm_code: Optional[str] = Field(None, description="RxNorm RxCUI")
    rxnorm_name: Optional[str] = None
    confidence: Optional[str] = None

class StructuredClinicalData(BaseModel):
    """Final structured output from agent"""
    patient_info: Optional[dict] = Field(default_factory=dict)
    diagnoses: List[DiagnosisCode] = Field(default_factory=list)
    medications: List[MedicationCode] = Field(default_factory=list)
    vital_signs: Optional[VitalSigns] = None
    lab_results: List[str] = Field(default_factory=list)
    plan_actions: List[str] = Field(default_factory=list)
```

**Estimated time:** 8 minutes

---

### 3.2 Create Agent with Tools

**Set up agent using OpenAI Agents SDK:**

```python
from agents import Agent, Runner

# Create extraction agent
extraction_agent = Agent(
    name="Clinical Data Extraction Agent",
    instructions="""
    You are a medical data extraction specialist. Your job is to:
    1. Extract clinical entities from medical notes (diagnoses, medications, vitals, labs, plans)
    2. Enrich diagnoses with ICD-10-CM codes using the lookup_icd10_code tool
    3. Enrich medications with RxNorm codes using the lookup_rxnorm_code tool
    4. Return structured data in the specified format

    Process:
    - First, extract raw entities from the note text
    - For each diagnosis, call lookup_icd10_code to get ICD-10-CM codes
    - For each medication, call lookup_rxnorm_code to get RxNorm codes
    - Compile everything into the structured output format

    Be thorough but efficient. Handle missing data gracefully.
    """,
    tools=[extract_clinical_entities, lookup_icd10_code, lookup_rxnorm_code],
    output_type=StructuredClinicalData,  # Structured output
)
```

**Estimated time:** 5 minutes

---

### 3.3 Test Agent with SOAP Notes

**Run agent on sample notes and iterate:**

```python
import asyncio

async def test_extraction(soap_note: str):
    result = await Runner.run(
        extraction_agent,
        input=f"Extract and enrich clinical data from this medical note:\n\n{soap_note}"
    )
    return result.final_output

# Test with SOAP note 01
with open("../../med_docs/soap/soap_01.txt") as f:
    soap_01 = f.read()

result = await test_extraction(soap_01)
print(result.model_dump_json(indent=2))
```

**Testing checklist:**

- Run on 2-3 different SOAP notes
- Verify diagnoses have ICD-10-CM codes
- Verify medications have RxNorm codes
- Check for errors or missing data
- Iterate on agent instructions if needed

**Estimated time:** 12 minutes

---

## Phase 4: Integrate into Backend (35 minutes)

### 4.1 Create Agent Service Module

**File:** `backend/app/services/agent_extraction.py`

**Implementation:**

- Copy tool functions from notebook
- Copy agent setup from notebook
- Add `ExtractorService` class (singleton pattern like LLM service)
- Key method: `async def extract_structured_data(note_text: str) -> StructuredClinicalData`
- Add error handling and logging
- Reuse existing OpenAI client configuration

**Estimated time:** 12 minutes

---

### 4.2 Create Pydantic Schemas for API

**File:** `backend/app/schemas/extraction.py`

**Implementation:**

- Copy Pydantic models from notebook:
  - `VitalSigns`
  - `DiagnosisCode`
  - `MedicationCode`
  - `StructuredClinicalData`
- Add request schema:
  - `ExtractionRequest` with `text` field
- Add response schema with metadata:
  - `ExtractionResponse` extending `StructuredClinicalData`
  - Add `processing_time_ms`, `model_used`, etc.

**Estimated time:** 8 minutes

---

### 4.3 Create API Endpoint

**File:** `backend/app/api/routes/extraction.py`

**Implementation:**

```python
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.extraction import ExtractionRequest, ExtractionResponse
from app.services.agent_extraction import get_extractor_service

router = APIRouter()

@router.post("/extract_structured", response_model=ExtractionResponse)
async def extract_structured_data(request: ExtractionRequest):
    """
    Extract structured clinical data from medical note using agent workflow.
    Enriches diagnoses with ICD-10-CM codes and medications with RxNorm codes.
    """
    extractor = get_extractor_service()
    result = await extractor.extract_structured_data(request.text)
    return result
```

**Key features:**

- Accept raw medical note text
- Call agent service
- Return structured data with codes
- Add proper error handling (400, 500, 503)
- Add timing metrics

**Estimated time:** 10 minutes

---

### 4.4 Register Router and Test

**File:** `backend/app/main.py`

**Changes:**

- Import extraction router
- Add `app.include_router(extraction.router, prefix="/agent", tags=["Agent Extraction"])`
- Test endpoint in Swagger UI

**Testing:**

- Start server
- Test `POST /agent/extract_structured` with SOAP note
- Verify structured output with codes
- Test error handling (empty text, invalid input)

**Estimated time:** 5 minutes

---

## Phase 5: Documentation & Testing (20 minutes)

### 5.1 Add Inline Documentation

- Add docstrings to all agent service functions
- Add comments explaining agent workflow
- Document API schemas with examples

**Estimated time:** 5 minutes

---

### 5.2 Create Test Notebook/Script

**File:** `backend/notebooks/test_extraction_endpoint.ipynb` or `backend/tests/test_agent_extraction.py`

**Test cases:**

- Test with all 6 SOAP notes
- Verify ICD-10-CM codes are returned for diagnoses
- Verify RxNorm codes are returned for medications
- Verify vital signs are extracted
- Test edge cases (notes with no diagnoses, no medications, etc.)
- Validate output schema

**Estimated time:** 10 minutes

---

### 5.3 Update README

**File:** `backend/README.md`

**Add section:**

- "Agent for Structured Data Extraction" overview
- Document POST `/agent/extract_structured` endpoint
- Show example request/response with ICD and RxNorm codes
- List public APIs used (NLM Clinical Tables, RxNav)
- Update project status to mark Part 4 complete

**Estimated time:** 5 minutes

---

## Implementation Order

**Recommended sequence:**

1. **Setup** (10 min)

   - Install dependencies
   - Create notebook structure
   - Test API access

2. **Notebook Prototyping** (55 min)

   - Build function tools one by one
   - Test each tool independently
   - Define Pydantic schemas
   - Create agent with tools
   - Test agent on SOAP notes
   - Iterate until working well

3. **Backend Integration** (35 min)

   - Copy working code to service module
   - Create API schemas
   - Build endpoint
   - Register router
   - Test via Swagger UI

4. **Documentation** (20 min)
   - Add docstrings
   - Create test cases
   - Update README

---

## Success Criteria

- [ ] OpenAI Agents SDK installed and working
- [ ] Notebook demonstrates agent extracting data from SOAP notes
- [ ] ICD-10-CM codes returned for diagnoses (using NLM API)
- [ ] RxNorm codes returned for medications (using NLM API)
- [ ] Structured output validated with Pydantic
- [ ] `POST /agent/extract_structured` endpoint working in backend
- [ ] Endpoint tested with multiple SOAP notes
- [ ] Documentation updated with examples
- [ ] Agent handles errors gracefully (missing data, API failures)

---

## Time Allocation Summary

| Phase                   | Time        |
| ----------------------- | ----------- |
| Setup & Dependencies    | 10 min      |
| Define Function Tools   | 30 min      |
| Build Agent (Notebook)  | 25 min      |
| Integrate into Backend  | 35 min      |
| Documentation & Testing | 20 min      |
| **Total**               | **2 hours** |

---

## Key Design Decisions

### Why OpenAI Agents SDK?

- ✅ Lightweight, official framework from OpenAI
- ✅ Native support for function tools and structured outputs
- ✅ Clean abstraction for agent workflows
- ✅ Well-documented and actively maintained (2025)
- ✅ Handles tool calling orchestration automatically

### Why Jupyter Notebook First?

- ✅ Interactive development and testing
- ✅ Easy to iterate on prompts and agent instructions
- ✅ Can visualize outputs before committing to API structure
- ✅ Serves as living documentation
- ✅ Fast feedback loop for tool development

### Why NLM Clinical Tables + RxNav?

- ✅ Free, no authentication required
- ✅ Official NIH/NLM APIs (reliable, maintained)
- ✅ Purpose-built for medical code lookup
- ✅ Fast autocomplete-style responses
- ✅ Handle fuzzy matching (typos, variations)

### Agent Workflow Strategy

1. **Single agent with multiple tools** (not multi-agent handoff)
   - Simpler for 2-hour timeline
   - Agent orchestrates all tools itself
2. **Sequential tool calling**
   - Extract entities first
   - Then enrich with codes
   - Compile final output
3. **Structured output** with Pydantic
   - Use `output_type` parameter in Agent
   - Ensures consistent, validated responses

---

## Potential Challenges & Mitigations

| Challenge                                   | Mitigation                                            |
| ------------------------------------------- | ----------------------------------------------------- |
| OpenAI Agents SDK is new/unfamiliar         | Test in notebook first, start with simple examples    |
| External API calls may be slow              | Add timeouts, handle failures gracefully              |
| ICD/RxNorm APIs may return multiple matches | Return top result, include confidence score           |
| Agent may make too many tool calls          | Optimize agent instructions, batch when possible      |
| Notebook → backend code conversion          | Keep notebook code clean, use functions not notebooks |
| Complex medical terminology                 | Rely on fuzzy matching in external APIs               |

---

## API Details

### NLM Clinical Tables API (ICD-10-CM)

**Endpoint:** `https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search`

**Parameters:**

- `sf=code,name` - Return code and name fields
- `terms={condition}` - Search term
- `maxList=1` - Return only top result

**Response format:**

```json
[
  1,
  ["E11.9"],
  null,
  [["E11.9", "Type 2 diabetes mellitus without complications"]]
]
```

---

### NLM RxNav API (RxNorm)

**Exact match:** `https://rxnav.nlm.nih.gov/REST/rxcui.json?name={medication}`

**Approximate match:** `https://rxnav.nlm.nih.gov/REST/approximateTerm.json?term={medication}`

**Response format (exact):**

```json
{
  "idGroup": {
    "rxnormId": ["860975"]
  }
}
```

**Then get details:** `https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/property.json?propName=RxNorm%20Name`

---

## Testing Strategy

### Notebook Testing (Manual)

1. Test each tool independently with sample inputs
2. Test agent with 2-3 SOAP notes
3. Verify codes are returned and look reasonable
4. Check for missing data handling

### Backend Testing (Manual + API)

1. Test endpoint via Swagger UI with all 6 SOAP notes
2. Verify response structure matches schema
3. Test error cases (empty text, invalid input)
4. Verify performance (<10s for typical note)

### Optional Automated Tests (if time permits)

- Mock external API calls for unit tests
- Test Pydantic schema validation
- Test error handling paths

---

## Stretch Goals (if time permits)

- [ ] Add confidence scoring for extracted entities
- [ ] Handle multiple ICD codes per diagnosis (return top 3)
- [ ] Add caching for API calls (same diagnosis/med appears multiple times)
- [ ] Add WHO ICD-11 API as optional tool
- [ ] Add openFDA API for medication warnings/recalls
- [ ] Stream agent progress updates to frontend
- [ ] Add agent tracing/logging for debugging

---

## Notes & Reminders

- **Keep agent instructions clear and specific** - be explicit about the workflow
- **Test tools independently first** - ensure each works before combining
- **Handle missing data gracefully** - not every note has all fields
- **Log all external API calls** - helps debug issues
- **Use async/await throughout** - agent and API calls are async
- **Reuse existing patterns** - service singleton, error handling, logging
- **Don't over-engineer** - single agent with tools is sufficient
- **Focus on working end-to-end** - polish can come later

---

## Next Steps (Post-Sprint)

After completing Part 4, the project will be ready for:

**Part 5:** FHIR Conversion

- Map structured data to FHIR resources (Patient, Condition, MedicationRequest, Observation)
- Create `POST /fhir/convert` endpoint
- Validate against FHIR spec

**Part 6:** Containerization

- Create Dockerfile for backend
- Complete docker-compose.yml (add backend service)
- Production-ready deployment
