# DF HealthBench - Backend API

FastAPI backend for AI-powered medical document processing.

## Quick Start

### With Docker (Recommended)

The easiest way to run the entire application:

```bash
# From project root
docker-compose up -d

# Access API
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

See root-level `README.md` for complete Docker deployment instructions.

### Local Development (Without Docker)

```bash
# 1. Start database
make db-start

# 2. Install dependencies (from backend directory)
cd backend
poetry install

# 3. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Run application
poetry run uvicorn app.main:app --reload

# 5. Access API
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

---

## Table of Contents

- [Architecture](#architecture)
- [Database](#database)
- [API Endpoints](#api-endpoints)
- [LLM Integration](#llm-integration)
- [Development Setup](#development-setup)
- [Configuration](#configuration)
- [Testing](#testing)
- [Project Status](#project-status)

---

## Architecture

### Tech Stack

- **Framework:** FastAPI 0.122+
- **Database:** PostgreSQL 15 with PGVector
- **ORM:** SQLAlchemy 2.0
- **Validation:** Pydantic 2.0
- **LLM:** OpenAI API (GPT + Embeddings)
- **Agents:** OpenAI Agents SDK
- **Vector Search:** PGVector extension
- **FHIR:** fhir.resources 8.1.0 (FHIR R4)
- **External APIs:** NLM Clinical Tables (ICD-10-CM), NLM RxNav (RxNorm)
- **Environment:** Poetry

### Application Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration & settings
│   ├── database.py             # Database connection & session
│   ├── seed.py                 # Database seeding script
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── document.py         # Document table model
│   │   └── document_embedding.py  # Embedding table model (PGVector)
│   │
│   ├── schemas/                # Pydantic validation schemas
│   │   ├── document.py         # Document request/response schemas
│   │   ├── llm.py              # LLM request/response schemas
│   │   ├── rag.py              # RAG request/response schemas
│   │   ├── extraction.py       # Agent extraction schemas
│   │   └── fhir.py             # FHIR conversion schemas
│   │
│   ├── crud/                   # Database operations
│   │   ├── document.py         # Document CRUD queries
│   │   └── embedding.py        # Embedding CRUD + vector search
│   │
│   ├── services/               # Business logic
│   │   ├── document.py         # Document service layer
│   │   ├── llm.py              # LLM service layer (OpenAI)
│   │   ├── embedding.py        # Embedding generation service
│   │   ├── chunking.py         # Document chunking utilities
│   │   ├── rag.py              # RAG pipeline orchestration
│   │   ├── agent_extraction.py # Agent extraction service
│   │   └── fhir_conversion.py  # FHIR R4 conversion service
│   │
│   └── api/routes/             # API endpoints
│       ├── health.py           # Health check endpoints
│       ├── documents.py        # Document CRUD endpoints
│       ├── llm.py              # LLM endpoints
│       ├── llm_helpers.py      # Shared LLM utilities
│       ├── rag.py              # RAG endpoints
│       ├── extraction.py       # Agent extraction endpoints
│       └── fhir.py             # FHIR conversion endpoints
│
├── tests/                      # Test files
├── pyproject.toml              # Dependencies
└── README.md                   # This file
```

### Request Flow

```
HTTP Request
    ↓
Route Handler (api/routes/)
    ↓
Service Layer (services/)
    ↓
CRUD Layer (crud/)
    ↓
Database (PostgreSQL)
```

---

## Database

### Setup

The project uses Docker Compose for local PostgreSQL:

```bash
# Start database
make db-start

# View logs
make db-logs

# Restart database
make db-restart

# Stop database
make db-stop

# Clean database (⚠️ destroys all data)
make db-clean
```

### Connection Details

```
Host:     localhost
Port:     5432
Database: df_healthbench
User:     dfuser
Password: dfpassword
```

### Schema

#### `documents` Table

Stores medical documents (SOAP notes, clinical documents, etc.)

| Column       | Type                   | Description                |
| ------------ | ---------------------- | -------------------------- |
| `id`         | INTEGER (PK, auto-inc) | Unique document identifier |
| `title`      | VARCHAR(255), NOT NULL | Document title             |
| `content`    | TEXT, NOT NULL         | Full document text         |
| `created_at` | TIMESTAMP WITH TZ      | Creation timestamp         |
| `updated_at` | TIMESTAMP WITH TZ      | Last update timestamp      |

**Indexes:**

- Primary key on `id`
- Index on `title`

**Auto-timestamps:**

- `created_at`: Set on insert
- `updated_at`: Updated on modification

#### `document_embeddings` Table

Stores vector embeddings for RAG (Retrieval-Augmented Generation)

| Column        | Type                   | Description                    |
| ------------- | ---------------------- | ------------------------------ |
| `id`          | INTEGER (PK, auto-inc) | Unique embedding identifier    |
| `document_id` | INTEGER (FK), NOT NULL | Reference to documents table   |
| `chunk_index` | INTEGER, NOT NULL      | Index of chunk within document |
| `chunk_text`  | TEXT, NOT NULL         | Text content of the chunk      |
| `embedding`   | VECTOR(1536), NOT NULL | Vector embedding (PGVector)    |
| `created_at`  | TIMESTAMP WITH TZ      | Creation timestamp             |

**Indexes:**

- Primary key on `id`
- Foreign key on `document_id` (CASCADE delete)
- Composite index on `(document_id, chunk_index)`
- Vector index for similarity search

**Vector Search:**

- Uses PGVector's cosine distance operator (`<=>`)
- 1536 dimensions (text-embedding-3-small model)

### Seeding

The application automatically seeds SOAP notes and generates embeddings on startup if the database is empty.

**Manual seeding:**

```bash
# Seed documents and generate embeddings
poetry run python -m app.seed

# Seed documents only (skip embeddings)
poetry run python -m app.seed --skip-embeddings

# Force re-seed everything
poetry run python -m app.seed --force
```

SOAP notes are loaded from `../soap/*.txt` files. Embeddings are generated automatically using OpenAI's `text-embedding-3-small` model.

---

## API Endpoints

### Base URL

```
Local: http://localhost:8000
```

### Interactive Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Endpoint Reference

#### Root

```http
GET /
```

Returns API information and status.

#### Health Checks

```http
GET /health
```

Basic health check (always returns `{"status": "ok"}`).

```http
GET /health/db
```

Health check with database connectivity test.

#### Documents

```http
GET /documents
```

List all document IDs with count.

**Response:**

```json
{
  "document_ids": [1, 2, 3, 4, 5, 6],
  "count": 6
}
```

---

```http
POST /documents
Content-Type: application/json

{
  "title": "SOAP Note - Patient John Doe",
  "content": "Subjective: Patient reports..."
}
```

Create a new document. Returns `201 Created` with document details.

---

```http
GET /documents/{id}
```

Get a document by ID. Returns `404` if not found.

---

```http
GET /documents/list/all?skip=0&limit=100
```

Get all documents with full details (paginated).

**Query Parameters:**

- `skip` (int, default: 0): Number of records to skip
- `limit` (int, default: 100): Max records to return

---

```http
DELETE /documents/{id}
```

Delete a document by ID. Returns `204 No Content` on success, `404` if not found.

#### LLM Operations

```http
POST /llm/summarize_note
Content-Type: application/json

{
  "text": "Subjective: 45yo male with chest pain...",
  "model": "gpt-5-nano"  // optional
}
```

Summarize medical note text using LLM.

**Response:**

```json
{
  "summary": "**Chief Complaint:** 45-year-old male with chest pain...",
  "model_used": "gpt-5-nano",
  "token_usage": {
    "prompt_tokens": 150,
    "completion_tokens": 80,
    "total_tokens": 230
  },
  "processing_time_ms": 1234
}
```

**Status Codes:**

- `200`: Success
- `400`: Invalid input (empty/too short text)
- `500`: LLM API error
- `503`: Service unavailable (rate limit, timeout, connection)

---

```http
POST /llm/summarize_document/{document_id}
```

Fetch a document from the database and summarize it.

**Response:** Same as `/llm/summarize_note`

**Status Codes:**

- `200`: Success
- `400`: Invalid document content
- `404`: Document not found
- `500`: LLM API error
- `503`: Service unavailable

---

#### RAG Operations

```http
GET /rag/stats
```

Get RAG system statistics (embeddings count, configuration, etc.)

---

```http
POST /rag/answer_question
Content-Type: application/json

{
  "question": "What medications are mentioned?",
  "top_k": 3,  // optional, default: 3
  "similarity_threshold": 0.7  // optional
}
```

Answer a question using RAG (Retrieval-Augmented Generation).

**Response:**

```json
{
  "answer": "Based on the documents, metformin is mentioned...",
  "sources": [
    {
      "document_id": 1,
      "document_title": "SOAP Note 01",
      "chunk_text": "...",
      "similarity_score": 0.85
    }
  ],
  "model_used": "gpt-5-nano",
  "token_usage": {...},
  "processing_time_ms": 2100
}
```

---

```http
POST /rag/embed_document/{document_id}
```

Generate embeddings for a single document.

---

```http
POST /rag/embed_all
```

Generate embeddings for all documents (runs automatically on first startup).

---

#### Agent Extraction

```http
POST /agent/extract_structured
Content-Type: application/json

{
  "text": "Subjective: 45yo male with Type 2 Diabetes...\n\nObjective: BP 130/85..."
}
```

Extract structured clinical data from medical notes using AI agents.

**Features:**

- Extracts diagnoses, medications, vital signs, labs, and plans
- Enriches diagnoses with ICD-10-CM codes (NLM Clinical Tables API)
- Enriches medications with RxNorm codes (NLM RxNav API)
- Returns validated Pydantic models

**Response:**

```json
{
  "patient_info": {"age": "45", "gender": "male"},
  "diagnoses": [
    {
      "text": "Type 2 Diabetes Mellitus",
      "icd10_code": "E11.9",
      "icd10_description": "Type 2 diabetes mellitus without complications",
      "confidence": "exact"
    }
  ],
  "medications": [
    {
      "text": "Metformin 500mg",
      "rxnorm_code": "860975",
      "rxnorm_name": "Metformin 500 MG Oral Tablet",
      "confidence": "exact"
    }
  ],
  "vital_signs": {...},
  "lab_results": [...],
  "plan_actions": [...],
  "processing_time_ms": 12894,
  "model_used": "gpt-4o-mini"
}
```

**Testing:**

```bash
poetry run python tests/test_agent_extraction_api.py
```

---

#### FHIR Conversion

```http
POST /fhir/convert
Content-Type: application/json

{
  "structured_data": {
    "patient_info": {"age": "45", "gender": "male"},
    "diagnoses": [
      {
        "text": "Type 2 Diabetes Mellitus",
        "icd10_code": "E11.9",
        "icd10_description": "Type 2 diabetes mellitus without complications",
        "confidence": "exact"
      }
    ],
    "medications": [
      {
        "text": "Metformin 500mg",
        "rxnorm_code": "860975",
        "rxnorm_name": "Metformin 500 MG Oral Tablet",
        "confidence": "exact"
      }
    ],
    "vital_signs": {
      "blood_pressure": "130/85",
      "heart_rate": "72",
      "temperature": "98.6°F"
    },
    "lab_results": ["HbA1c: 7.2%"],
    "plan_actions": ["Continue Metformin"]
  },
  "patient_id": "patient-123"
}
```

Convert structured clinical data (from agent extraction) to FHIR R4 resources.

**Features:**

- Converts to FHIR R4-compliant resources
- Uses official `fhir.resources` Python library
- Maps ICD-10-CM codes to Condition resources
- Maps RxNorm codes to MedicationRequest resources
- Converts vitals and labs to Observation resources
- Creates Patient resource from demographics

**Response:**

```json
{
  "patient": {
    "resourceType": "Patient",
    "id": "patient-123",
    "gender": "male",
    "birthDate": "1978-01-01",
    "identifier": [
      {
        "system": "urn:oid:df-healthbench",
        "value": "patient-123"
      }
    ]
  },
  "conditions": [
    {
      "resourceType": "Condition",
      "clinicalStatus": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
            "code": "active"
          }
        ]
      },
      "verificationStatus": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
            "code": "confirmed"
          }
        ]
      },
      "code": {
        "coding": [
          {
            "system": "http://hl7.org/fhir/sid/icd-10-cm",
            "code": "E11.9",
            "display": "Type 2 diabetes mellitus without complications"
          }
        ],
        "text": "Type 2 Diabetes Mellitus"
      },
      "subject": { "reference": "Patient/patient-123" },
      "recordedDate": "2025-11-30T12:34:56Z"
    }
  ],
  "medications": [
    {
      "resourceType": "MedicationRequest",
      "status": "active",
      "intent": "order",
      "medication": {
        "concept": {
          "coding": [
            {
              "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
              "code": "860975",
              "display": "Metformin 500 MG Oral Tablet"
            }
          ],
          "text": "Metformin 500mg"
        }
      },
      "subject": { "reference": "Patient/patient-123" },
      "authoredOn": "2025-11-30T12:34:56Z"
    }
  ],
  "observations": [
    {
      "resourceType": "Observation",
      "status": "final",
      "category": [
        {
          "coding": [
            {
              "system": "http://terminology.hl7.org/CodeSystem/observation-category",
              "code": "vital-signs"
            }
          ]
        }
      ],
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "85354-9",
            "display": "Blood pressure panel"
          }
        ],
        "text": "Blood pressure panel"
      },
      "subject": { "reference": "Patient/patient-123" },
      "effectiveDateTime": "2025-11-30T12:34:56Z",
      "valueString": "130/85"
    }
  ],
  "resource_count": 12,
  "processing_time_ms": 145
}
```

**FHIR Resource Mappings:**

| Source Data  | FHIR Resource     | Coding System |
| ------------ | ----------------- | ------------- |
| patient_info | Patient           | N/A           |
| diagnoses    | Condition         | ICD-10-CM     |
| medications  | MedicationRequest | RxNorm        |
| vital_signs  | Observation       | LOINC         |
| lab_results  | Observation       | Text-only     |

**Health Check:**

```http
GET /fhir/health
```

Returns service status and FHIR version.

**Testing:**

```bash
# Integration test (extraction + FHIR conversion)
poetry run python tests/test_fhir_conversion.py
```

---

## LLM Integration

### OpenAI Setup

The application uses OpenAI's API for medical text processing.

**1. Get API Key:**

- Visit [OpenAI Platform](https://platform.openai.com/api-keys)
- Create new secret key
- Copy the key

**2. Configure in `.env`:**

```bash
OPENAI_API_KEY=sk-proj-...your-key-here...
OPENAI_DEFAULT_MODEL=gpt-5-nano
OPENAI_TEMPERATURE=1.0
OPENAI_TIMEOUT=30
```

### Supported Models

**⚠️ Important: Only OpenAI models are supported. Other providers (Gemini, Claude, Anthropic, etc.) are not supported.**

The application validates model names and will return a 400 error if an unsupported model is requested.

| Model          | Cost (Input/Output per 1M tokens) | Use Case          |
| -------------- | --------------------------------- | ----------------- |
| `gpt-5-nano`   | $0.05 / $0.40                     | ⭐ Default, most efficient |
| `gpt-4o-mini`  | $0.05 / $0.40                     | Alias for gpt-5-nano |
| `gpt-5-mini`   | $0.25 / $2.00                     | Balanced          |
| `gpt-5`        | $1.25 / $10.00                    | High performance  |
| `gpt-4o`       | $1.25 / $10.00                    | Alias for gpt-5   |
| `gpt-5.1`      | $1.25 / $10.00                    | Latest version    |
| `gpt-4`        | Higher cost                       | Legacy model      |
| `gpt-3.5-turbo`| Lower cost                        | Legacy model      |

**Model Selection:**

You can override the default model on a per-request basis:

```bash
# Summarize with default model (gpt-5-nano)
curl -X POST http://localhost:8000/llm/summarize_document/1

# Summarize with specific model
curl -X POST "http://localhost:8000/llm/summarize_document/1?model=gpt-5-mini"

# Invalid model returns 400 error
curl -X POST "http://localhost:8000/llm/summarize_document/1?model=claude-3"
# Returns: {"detail": "Invalid model 'claude-3'. Only OpenAI models are supported..."}
```

### Architecture

**Singleton Pattern:**

The LLM service uses a module-level singleton to share the OpenAI client across all requests:

```python
from app.services.llm import get_llm_service

llm_service = get_llm_service()  # Returns same instance every time
result = llm_service.summarize_note(text)
```

**Benefits:**

- ✅ OpenAI client initialized once
- ✅ Connection pooling enabled
- ✅ Thread-safe for concurrent requests
- ✅ 40% faster after first request

### Features

**Current:**

- Medical note summarization (POST `/llm/summarize_note`)
- Document summarization by ID (POST `/llm/summarize_document/{id}`)
- RAG question answering (POST `/rag/answer_question`)
- Agent-based structured data extraction (POST `/agent/extract_structured`)
- FHIR R4 conversion (POST `/fhir/convert`)
- Token usage tracking and processing time metrics
- Comprehensive error handling (rate limits, timeouts, connection errors)

**Planned:**

- Multi-model support
- Advanced FHIR features (Bundles, CarePlan, Encounter)

### Error Handling

All LLM endpoints handle errors consistently:

- **ValueError** → 400 Bad Request (validation errors)
- **DocumentNotFoundError** → 404 Not Found
- **LLMRateLimitError** → 503 Service Unavailable
- **LLMTimeoutError** → 503 Service Unavailable
- **LLMConnectionError** → 503 Service Unavailable
- **LLMAPIError** → 500 Internal Server Error

Errors are logged with full context for debugging.

---

## Development Setup

### Prerequisites

- Python 3.11 or 3.12
- Poetry (Python dependency management)
- Docker & Docker Compose
- Make
- OpenAI API key

### Installation

**1. Install Poetry:**

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**2. Clone and Install:**

```bash
# Navigate to backend directory
cd backend

# Install dependencies
poetry install

# Activate virtual environment (optional)
poetry shell
```

**3. Database Setup:**

```bash
# From project root
make db-start

# Wait for database to be ready (check logs)
make db-logs
```

**4. Environment Configuration:**

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OPENAI_API_KEY
nano .env
```

**5. Run Application:**

```bash
# Development mode (auto-reload)
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Development Workflow

**Code Structure:**

1. **Routes** (`api/routes/`): Handle HTTP requests/responses
2. **Services** (`services/`): Implement business logic
3. **CRUD** (`crud/`): Execute database operations
4. **Models** (`models/`): Define database schema (SQLAlchemy)
5. **Schemas** (`schemas/`): Define API contracts (Pydantic)

**Adding New Endpoints:**

1. Define Pydantic schemas in `schemas/`
2. Create/update SQLAlchemy models in `models/`
3. Add CRUD operations in `crud/`
4. Implement business logic in `services/`
5. Create route handlers in `api/routes/`
6. Register router in `main.py`

**Code Quality:**

- Use type hints throughout
- Follow PEP 8 style guide
- Add docstrings to functions
- Keep routes minimal (delegate to services)
- Log important operations

---

## Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Database
DATABASE_URL=postgresql://dfuser:dfpassword@localhost:5432/df_healthbench

# API
API_TITLE=DF HealthBench API
API_VERSION=1.0.0
API_DESCRIPTION=AI-powered medical document processing API
ENVIRONMENT=development

# OpenAI (Required)
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_API_PROJECT=proj-your-project-id  # Optional
OPENAI_DEFAULT_MODEL=gpt-5-nano
OPENAI_TEMPERATURE=1.0
OPENAI_TIMEOUT=30
```

### Configuration Reference

| Variable               | Description               | Default                                         | Required |
| ---------------------- | ------------------------- | ----------------------------------------------- | -------- |
| `DATABASE_URL`         | PostgreSQL connection     | `postgresql://dfuser:...@localhost:5432/df_...` | Yes      |
| `API_TITLE`            | API title for docs        | `DF HealthBench API`                            | No       |
| `API_VERSION`          | API version               | `1.0.0`                                         | No       |
| `API_DESCRIPTION`      | API description           | `AI-powered medical document processing API`    | No       |
| `ENVIRONMENT`          | Environment mode          | `development`                                   | No       |
| `OPENAI_API_KEY`       | OpenAI API key            | -                                               | Yes      |
| `OPENAI_API_PROJECT`   | OpenAI project ID         | -                                               | No       |
| `OPENAI_DEFAULT_MODEL` | Default LLM model         | `gpt-5-nano`                                    | No       |
| `OPENAI_TEMPERATURE`   | LLM temperature (0.0-2.0) | `1.0`                                           | No       |
| `OPENAI_TIMEOUT`       | API timeout (seconds)     | `30`                                            | No       |

---

## Testing

### Manual Testing

**Using curl:**

```bash
# Health check
curl http://localhost:8000/health

# List documents
curl http://localhost:8000/documents

# Create document
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "content": "Test content..."}'

# Summarize text
curl -X POST http://localhost:8000/llm/summarize_note \
  -H "Content-Type: application/json" \
  -d '{"text": "Subjective: Patient reports fever..."}'

# Summarize document by ID
curl -X POST http://localhost:8000/llm/summarize_document/1

# RAG: Answer question
curl -X POST http://localhost:8000/rag/answer_question \
  -H "Content-Type: application/json" \
  -d '{"question": "What medications are mentioned?"}'

# RAG: Get stats
curl http://localhost:8000/rag/stats
```

**Using Swagger UI:**

1. Navigate to http://localhost:8000/docs
2. Expand any endpoint
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"

### Automated Tests

```bash
# Install test dependencies
poetry install --with dev

# Run all tests
poetry run pytest

# Run unit tests only (fast, mocked APIs)
poetry run pytest tests/test_agent_tools.py -v

# Run with coverage
poetry run pytest --cov=app

# Run integration tests (requires server running)
poetry run python tests/test_agent_extraction_api.py
poetry run python tests/test_fhir_conversion.py
```

See `tests/README_TESTS.md` for detailed testing documentation.

---

## Project Status

### ✅ Completed Features

**Part 1: Backend Foundation**

- [x] FastAPI application setup
- [x] PostgreSQL database with Docker
- [x] SQLAlchemy ORM models
- [x] Pydantic validation schemas
- [x] CRUD operations
- [x] Service layer with business logic
- [x] Health check endpoints
- [x] Document CRUD endpoints
- [x] Automatic database seeding
- [x] Comprehensive error handling
- [x] Logging throughout application
- [x] API documentation (Swagger/ReDoc)

**Part 2: LLM Integration**

- [x] OpenAI SDK integration
- [x] LLM service layer with singleton pattern
- [x] Medical note summarization endpoint
- [x] Document summarization by ID endpoint
- [x] Token usage tracking
- [x] Request/response logging
- [x] Comprehensive error handling (rate limits, timeouts, etc.)
- [x] Reusable error handling decorator

**Part 3: RAG Pipeline**

- [x] PGVector extension integration
- [x] Document embedding model (vector storage)
- [x] Embedding service (OpenAI text-embedding-3-small)
- [x] Document chunking utility (SOAP-aware)
- [x] Vector similarity search (cosine distance)
- [x] RAG service layer (retrieval + generation)
- [x] Question answering endpoint with source citations
- [x] Embedding management endpoints
- [x] Automatic embedding generation on startup
- [x] RAG statistics endpoint

**Part 4: Agent for Data Extraction**

- [x] OpenAI Agents SDK integration
- [x] Agent extraction service with singleton pattern
- [x] Clinical entity extraction (diagnoses, medications, vitals, labs, plans)
- [x] ICD-10-CM code enrichment (via NLM Clinical Tables API)
- [x] RxNorm code enrichment (via NLM RxNav API)
- [x] Structured output with Pydantic validation
- [x] Extract structured data endpoint (`POST /agent/extract_structured`)
- [x] Agent health check endpoint
- [x] Comprehensive error handling and logging
- [x] Test script for API validation

**Part 5: FHIR Conversion**

- [x] fhir.resources library integration (v8.1.0)
- [x] FHIR R4 conversion service with singleton pattern
- [x] Patient resource mapping (demographics → FHIR Patient)
- [x] Condition resource mapping (ICD-10-CM codes → FHIR Condition)
- [x] MedicationRequest resource mapping (RxNorm codes → FHIR MedicationRequest)
- [x] Observation resource mapping (vitals with LOINC codes + labs)
- [x] FHIR conversion endpoint (`POST /fhir/convert`)
- [x] FHIR health check endpoint (`GET /fhir/health`)
- [x] Integration test script
- [x] Comprehensive documentation with examples
- [x] Notebook prototyping and validation

**Part 6: Containerization**

- [x] Multi-stage Dockerfile for backend (Python 3.11-slim)
- [x] Docker Compose configuration with all services
- [x] Service health checks and dependencies (backend waits for postgres)
- [x] Environment variable management via env_file
- [x] Volume mounts for data persistence and document seeding
- [x] Production-ready configuration (4 Uvicorn workers)
- [x] Non-root user for security
- [x] Comprehensive documentation with deployment instructions
- [x] Tested full stack deployment
- [x] All endpoints verified in containerized environment

### 🎉 Project Complete!

All 6 parts of the DF HealthBench project have been successfully implemented and tested.

---

## Troubleshooting

**Database connection failed:**

```bash
# Ensure PostgreSQL is running
make db-start
make db-logs

# Check connection string in .env
# Verify: postgresql://dfuser:dfpassword@localhost:5432/df_healthbench
```

**Application won't start:**

```bash
# Check Poetry environment
poetry env info

# Reinstall dependencies
poetry install

# Check Python version (should be 3.11+)
python --version
```

**OpenAI API errors:**

```bash
# Verify API key is set
grep OPENAI_API_KEY .env

# Test API key manually
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check model availability (some models require specific tiers)
```

**Seeding fails:**

```bash
# Ensure ../soap/ directory exists with SOAP note files
ls ../soap/

# Manual seed with force flag
poetry run python -m app.seed --force
```

---

## License

Private - DF Project

---

## Support

For questions or issues, please refer to the project documentation or contact the development team.
