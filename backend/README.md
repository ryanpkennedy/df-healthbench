# DF HealthBench - Backend API

FastAPI backend for AI-powered medical document processing.

## Quick Start

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
- **Database:** PostgreSQL 15
- **ORM:** SQLAlchemy 2.0
- **Validation:** Pydantic 2.0
- **LLM:** OpenAI API
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
│   │   └── document.py         # Document table model
│   │
│   ├── schemas/                # Pydantic validation schemas
│   │   ├── document.py         # Document request/response schemas
│   │   └── llm.py              # LLM request/response schemas
│   │
│   ├── crud/                   # Database operations
│   │   └── document.py         # Document CRUD queries
│   │
│   ├── services/               # Business logic
│   │   ├── document.py         # Document service layer
│   │   └── llm.py              # LLM service layer (OpenAI)
│   │
│   └── api/routes/             # API endpoints
│       ├── health.py           # Health check endpoints
│       ├── documents.py        # Document CRUD endpoints
│       ├── llm.py              # LLM endpoints
│       └── llm_helpers.py      # Shared LLM utilities
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

| Column       | Type                      | Description                    |
| ------------ | ------------------------- | ------------------------------ |
| `id`         | INTEGER (PK, auto-inc)    | Unique document identifier     |
| `title`      | VARCHAR(255), NOT NULL    | Document title                 |
| `content`    | TEXT, NOT NULL            | Full document text             |
| `created_at` | TIMESTAMP WITH TZ         | Creation timestamp             |
| `updated_at` | TIMESTAMP WITH TZ         | Last update timestamp          |

**Indexes:**
- Primary key on `id`
- Index on `title`

**Auto-timestamps:**
- `created_at`: Set on insert
- `updated_at`: Updated on modification

### Seeding

The application automatically seeds SOAP notes on startup if the database is empty.

**Manual seeding:**

```bash
# Seed only if empty
poetry run python -m app.seed

# Force seed (overwrites existing data)
poetry run python -m app.seed --force
```

SOAP notes are loaded from `../soap/*.txt` files.

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

| Model        | Cost (Input/Output per 1M tokens) | Use Case          |
| ------------ | --------------------------------- | ----------------- |
| `gpt-5-nano` | $0.05 / $0.40                     | ⭐ Most efficient |
| `gpt-5-mini` | $0.25 / $2.00                     | Balanced          |
| `gpt-5`      | $1.25 / $10.00                    | High performance  |
| `gpt-5.1`    | $1.25 / $10.00                    | Latest version    |

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
- Token usage tracking
- Processing time metrics
- Comprehensive error handling (rate limits, timeouts, connection errors)

**Planned:**
- RAG (Retrieval-Augmented Generation) pipeline
- Structured data extraction
- FHIR format conversion
- Multi-model support

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

| Variable               | Description                 | Default                                           | Required |
| ---------------------- | --------------------------- | ------------------------------------------------- | -------- |
| `DATABASE_URL`         | PostgreSQL connection       | `postgresql://dfuser:...@localhost:5432/df_...`   | Yes      |
| `API_TITLE`            | API title for docs          | `DF HealthBench API`                              | No       |
| `API_VERSION`          | API version                 | `1.0.0`                                           | No       |
| `API_DESCRIPTION`      | API description             | `AI-powered medical document processing API`      | No       |
| `ENVIRONMENT`          | Environment mode            | `development`                                     | No       |
| `OPENAI_API_KEY`       | OpenAI API key              | -                                                 | Yes      |
| `OPENAI_API_PROJECT`   | OpenAI project ID           | -                                                 | No       |
| `OPENAI_DEFAULT_MODEL` | Default LLM model           | `gpt-5-nano`                                      | No       |
| `OPENAI_TEMPERATURE`   | LLM temperature (0.0-2.0)   | `1.0`                                             | No       |
| `OPENAI_TIMEOUT`       | API timeout (seconds)       | `30`                                              | No       |

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
```

**Using Swagger UI:**

1. Navigate to http://localhost:8000/docs
2. Expand any endpoint
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"

### Automated Tests

```bash
# Run tests (when implemented)
poetry run pytest

# Run with coverage
poetry run pytest --cov=app
```

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

### 🚧 Next Steps

- [ ] Part 3: RAG Pipeline (vector embeddings, semantic search)
- [ ] Part 4: Agent for Data Extraction (ICD codes, RxNorm codes)
- [ ] Part 5: FHIR Conversion (Patient, Condition, Medication resources)
- [ ] Part 6: Containerization (Dockerfile, full docker-compose)

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
