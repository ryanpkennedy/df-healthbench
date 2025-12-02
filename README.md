# DF HealthBench

AI-powered medical document processing system using LLMs, RAG, and FHIR standards. This README discusses startup, testing, and basic app functionality. See `backend/README.md` for comprehensive backend documentation

To view a quick summary of all of the project tasks that were complete, refer to `project_completion.md` in this repo. A detailed breakdown of how I completed each task is available in the `/sprints` folder.

## Quick Start with Docker

The easiest way to run the entire application is with the Make command or Docker Compose. Make sure .env is ready to go then simply run `make fresh-start` to start the backend, db and seed the db. If you ever want to reset the db, and have a clean start with the app, you can rerun `make fresh-start`. 

Once the app is up and running, then `make test` will run the full pytest test suite. A more granular approach is shown below.

#### 1. Ensure Docker and Docker Compose are installed

```bash
docker --version
docker-compose --version
```

#### 2. Environment Variable Setup

Copy the `backend/.env.example` into a `backend/.env` and make sure to add your own OpenAI API key. There are 2 different database connection strings based on whether you are running the backend via docker (default) or on its own via uvicorn, since the backend needs to reference the db server name differently depending on if it is running in the same docker network or not.

#### 3. Start all services (database + backend)

```bash
make up
```

or

```bash
docker-compose up -d
```

#### 4. View logs

```bash
docker-compose logs -f
```

#### 5. Access the application

- API: http://localhost:8000

- Interactive API docs: http://localhost:8000/docs

- ReDoc: http://localhost:8000/redoc

### First Time Setup

The application will automatically:

- Initialize PostgreSQL with PGVector extension
- Create database tables
- Seed documents from `med_docs/soap/` (SOAP notes) and `med_docs/policy/` (PDF policies)
- Generate vector embeddings for RAG

This takes about 30-60 seconds on first startup.

### Adding New Documents

To add new medical documents:

1. Add `.txt` or `.pdf` files to `med_docs/soap/` or `med_docs/policy/`
2. Restart the application: `docker-compose restart backend`
3. The system will automatically detect and seed new documents
4. View logs to confirm: `docker-compose logs -f backend | grep -i seed`

Or manually trigger re-seeding:

```bash
docker-compose exec backend python -m app.seed
```

## Testing the Backend Endpoints

#### Manual Testing

The simplest way to interact with the endpoints is to go to http://localhost:8000/docs. This allows you to view all of the endpoints through a web UI, with instructions and example requests to try out.

It is helpful to view the log output while the backend is processing requests, to see what is going on in the backend. Use `docker-compose logs -f` to view backend logs.

#### Automated Testing

There is also a comprehensive pytest test suite with 140+ tests covering all 5 core project parts. See `add_docs/testing.md` for details. As previously mentioned, `make test` will run the whole test suite.

## What's Included

This project implements a complete medical document processing pipeline:

### Part 1: FastAPI Backend Foundation

- RESTful API with FastAPI
- PostgreSQL database with SQLAlchemy ORM
- Document CRUD operations
- Health check endpoints

### Part 2: LLM Integration

- OpenAI GPT integration
- Medical note summarization
- Token usage tracking

### Part 3: RAG Pipeline

- Vector embeddings with OpenAI text-embedding-3-small
- PGVector for similarity search
- Context-aware question answering
- Source citation

### Part 4: Agent for Structured Data Extraction

- AI agent for clinical entity extraction
- ICD-10-CM code enrichment (via NLM Clinical Tables API)
- RxNorm medication codes (via NLM RxNav API)
- Structured Pydantic output

### Part 5: FHIR Conversion

- FHIR R4 resource generation
- Patient, Condition, MedicationRequest, Observation resources
- Standard coding systems (ICD-10-CM, RxNorm, LOINC)

### Part 6: Containerization

- Production-ready Docker deployment
- Multi-stage Dockerfile for optimized images
- Health checks and service dependencies
- Persistent data storage

## API Endpoints

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Database connectivity check
curl http://localhost:8000/health/db
```

### Documents

```bash
# List all documents
curl http://localhost:8000/documents

# Get specific document
curl http://localhost:8000/documents/1
```

### LLM Operations

```bash
# Summarize a medical note
curl -X POST http://localhost:8000/llm/summarize_document/1

# Or with raw text
curl -X POST http://localhost:8000/llm/summarize_note \
  -H "Content-Type: application/json" \
  -d '{"text": "Subjective: Patient reports fever..."}'
```

### RAG (Question Answering)

```bash
# Get RAG system statistics
curl http://localhost:8000/rag/stats

# Ask a question
curl -X POST http://localhost:8000/rag/answer_question \
  -H "Content-Type: application/json" \
  -d '{"question": "What medications are mentioned?"}'
```

### Agent Extraction

```bash
# Extract structured data from medical note
curl -X POST http://localhost:8000/agent/extract_structured \
  -H "Content-Type: application/json" \
  -d '{"text": "Subjective: 45yo male with Type 2 Diabetes..."}'
```

### FHIR Conversion

Visit http://localhost:8000/docs and test the `/fhir/convert` endpoint interactively.

## Docker Commands

For convenience, use the provided Makefile commands:

```bash
# See all available commands
make help

# Common operations
make build              # Build images
make up                 # Start services
make logs               # View logs
make ps                 # Check status
make down               # Stop services

# Development with hot-reload
make dev-up             # Start dev environment
make dev-down           # Stop dev environment
```

Or use docker-compose directly:

```bash
# Start services (detached mode)
docker-compose up -d

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f backend
docker-compose logs -f postgres

# Check service status
docker-compose ps

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Clean restart (⚠️ destroys all data)
docker-compose down -v
docker-compose up -d --build

# Restart a specific service
docker-compose restart backend
```

## Environment Variables

The application uses environment variables from `backend/.env`:

**Required:**

- `OPENAI_API_KEY` - Your OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

**Optional:**

- `OPENAI_DEFAULT_MODEL` - Default LLM model (default: `gpt-4o-mini`)
- `OPENAI_TEMPERATURE` - LLM temperature 0.0-2.0 (default: `1.0`)
- `OPENAI_TIMEOUT` - API timeout in seconds (default: `30`)

See `backend/.env.example` for a complete template.

## Local Development (Without Docker)

If you prefer to run locally without Docker:

```bash
# 1. Start PostgreSQL with Docker
docker-compose up -d postgres

# 2. Install backend dependencies
cd backend
poetry install

# 3. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Run the application
poetry run uvicorn app.main:app --reload

# 5. Access at http://localhost:8000
```

See `backend/README.md` for detailed local development instructions.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Client/Browser                 │
│            http://localhost:8000                │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│           FastAPI Backend Container             │
│  ┌────────────────────────────────────────────┐ │
│  │  Routes → Services → CRUD → Database       │ │
│  │  • LLM Integration (OpenAI)                │ │
│  │  • RAG Pipeline (Embeddings + Search)      │ │
│  │  • Agent Extraction (ICD/RxNorm)           │ │
│  │  • FHIR Conversion (R4 Resources)          │ │
│  └────────────────────────────────────────────┘ │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│        PostgreSQL + PGVector Container          │
│  • Document storage                             │
│  • Vector embeddings (1536 dimensions)          │
│  • Similarity search                            │
│  • Persistent volume for data                   │
└─────────────────────────────────────────────────┘
```

## Tech Stack

- **Backend:** FastAPI 0.122+, Python 3.11
- **Database:** PostgreSQL 15 with PGVector extension
- **ORM:** SQLAlchemy 2.0
- **Validation:** Pydantic 2.0
- **LLM:** OpenAI API (GPT models)
- **Embeddings:** OpenAI text-embedding-3-small (1536 dimensions)
- **Agents:** OpenAI Agents SDK
- **FHIR:** fhir.resources 8.1.0 (R4 compliant)
- **Deployment:** Docker & Docker Compose

## Project Structure

```
df-healthbench/
├── docker-compose.yml          # Docker orchestration
├── med_docs/                   # Medical documents for seeding
│   ├── soap/                   # SOAP format notes
│   └── policy/                 # Policy documents
├── backend/                    # FastAPI application
│   ├── Dockerfile              # Backend container image
│   ├── app/                    # Application code
│   │   ├── main.py             # FastAPI entry point
│   │   ├── api/routes/         # API endpoints
│   │   ├── services/           # Business logic
│   │   ├── crud/               # Database operations
│   │   ├── models/             # SQLAlchemy models
│   │   └── schemas/            # Pydantic schemas
│   ├── tests/                  # Test files
│   ├── pyproject.toml          # Poetry dependencies
│   └── README.md               # Detailed backend docs
└── README.md                   # This file
```

## Testing

All endpoints are documented with OpenAPI/Swagger:

1. Start the application: `docker-compose up -d`
2. Visit http://localhost:8000/docs
3. Try out any endpoint interactively

Example test flow:

1. ✅ Health check: `GET /health`
2. ✅ List documents: `GET /documents` (should show 6-14 seeded documents)
3. ✅ RAG stats: `GET /rag/stats` (should show embeddings generated)
4. ✅ Ask question: `POST /rag/answer_question`
5. ✅ Extract data: `POST /agent/extract_structured`
6. ✅ Convert to FHIR: `POST /fhir/convert`

## Performance

- **Docker Image Size:** ~484MB (multi-stage build with Poetry)
- **Startup Time:** 30-60 seconds (includes DB init, seeding, embeddings)
- **Memory Usage:** ~300-500MB (4 Uvicorn workers)
- **RAG Query Time:** 10-20 seconds (including LLM generation)
- **Agent Extraction:** 10-30 seconds (depends on note complexity + external API calls)

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs backend
docker-compose logs postgres

# Verify .env file exists
ls -la backend/.env

# Rebuild from scratch
docker-compose down -v
docker-compose up -d --build
```

### OpenAI API errors

```bash
# Verify API key is set
cat backend/.env | grep OPENAI_API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Port already in use

```bash
# Check what's using port 8000
lsof -i :8000

# Change port in docker-compose.yml
# ports:
#   - "8001:8000"  # Maps host:container
```

### Database connection issues

```bash
# Ensure postgres is healthy
docker-compose ps

# Should show:
# df-healthbench-db      Up (healthy)
# df-healthbench-backend Up (healthy)

# If not healthy, check postgres logs
docker-compose logs postgres
```

## Documentation

- **Backend API:** See `backend/README.md` for comprehensive backend documentation
- **API Reference:** http://localhost:8000/docs (when running)
- **Sprint Plans:** See `backend/sprints/` for detailed implementation plans
- **Project Overview:** See `project_overview.md` for assignment details
