# DF HealthBench - Backend API

FastAPI backend for medical document processing using LLM technology.

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Validation:** Pydantic
- **Environment Management:** Poetry
- **LLM:** OpenAI API

## Architecture

```
Route (endpoint) → Service (business logic) → CRUD (DB operations) → Database
```

## Prerequisites

- Python 3.11 or 3.12
- Poetry (Python dependency management)
- Docker & Docker Compose (for local database)
- Make (for database management commands)

## Installation

### 1. Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Install Dependencies

```bash
cd backend
poetry install
```

### 3. Set up PostgreSQL Database

The project uses Docker Compose for local database management.

**Start the database:**

```bash
# From project root directory
make db-start
```

This will start a PostgreSQL container with the following configuration:

- Host: `localhost`
- Port: `5432`
- Database: `df_healthbench`
- User: `dfuser`
- Password: `dfpassword`

**Other database commands:**

```bash
make db-stop      # Stop the database
make db-restart   # Restart the database
make db-logs      # View database logs
make db-clean     # Stop and remove all data (WARNING: destructive)
```

### 4. Configure Environment

```bash
# Copy example env file (from backend directory)
cp .env.example .env

# The .env file is pre-configured to work with the Docker database
# You can edit .env if you need to change any settings
```

### 5. Set up OpenAI API (Required for Part 2+)

**Get your API key:**

1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Navigate to "API Keys" section
4. Click "Create new secret key"
5. Copy the generated key

**Add to your `.env` file:**

```bash
# Required
OPENAI_API_KEY=your-actual-api-key-here

# Optional (if using project-based organization)
OPENAI_API_PROJECT=your-project-id-here

# Optional - Model configuration (defaults shown)
OPENAI_DEFAULT_MODEL=gpt-5-nano  # Most cost-effective option
OPENAI_TEMPERATURE=1.0
OPENAI_TIMEOUT=30
```

**⚠️ Important:** Never commit your `.env` file or API keys to version control!

**Supported Models:**

- `gpt-5-nano` - Most cost-effective ($0.05/1M input, $0.40/1M output) ⭐ Recommended
- `gpt-5-mini` - Balanced performance ($0.25/1M input, $2.00/1M output)
- `gpt-5` - High performance ($1.25/1M input, $10.00/1M output)
- `gpt-5.1` - Latest version ($1.25/1M input, $10.00/1M output)

## Running the Application

### Start Database (if not already running)

```bash
# From project root
make db-start
```

### Development Server

```bash
# From backend directory
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access the API

- **API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## API Endpoints

### Health Check

- `GET /health` - Basic health check
- `GET /health/db` - Health check with database connectivity

### Documents

- `GET /documents` - List all document IDs with count
- `POST /documents` - Create a new document
- `GET /documents/{id}` - Get document by ID
- `GET /documents/list/all` - Get all documents with full details (paginated)
- `DELETE /documents/{id}` - Delete a document

### LLM

- `POST /llm/summarize_note` - Summarize a medical note using AI

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection setup
│   ├── seed.py              # Database seeding script
│   ├── models/
│   │   ├── __init__.py
│   │   └── document.py      # SQLAlchemy models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── document.py      # Pydantic schemas
│   ├── crud/
│   │   ├── __init__.py
│   │   └── document.py      # Database queries
│   ├── services/
│   │   ├── __init__.py
│   │   └── document.py      # Business logic
│   └── api/
│       ├── __init__.py
│       └── routes/
│           ├── __init__.py
│           ├── health.py    # Health check endpoints
│           └── documents.py # Document CRUD endpoints
├── test_db_setup.py         # Phase 3 test script
├── test_crud_service.py     # Phase 4 test script
├── .env                     # Environment variables (not in git)
├── .env.example             # Example environment variables
├── .gitignore
├── pyproject.toml           # Poetry dependencies
└── README.md
```

## Database Seeding

The application automatically seeds the database with SOAP notes on startup if the database is empty.

**Manual seeding:**

```bash
# Seed only if database is empty
poetry run python -m app.seed

# Force seed even if data exists
poetry run python -m app.seed --force
```

The seed script loads all SOAP note files from the `../soap/` directory.

## Testing

### Automated Test Scripts

**Test Database Setup (Phase 3):**

```bash
poetry run python test_db_setup.py
```

Tests: database connection, table creation, document insertion, schema validation

**Test CRUD & Services (Phase 4):**

```bash
poetry run python test_crud_service.py
```

Tests: CRUD operations, service layer, error handling, multiple documents

### Manual Testing with curl

**Health Check:**

```bash
# Basic health check
curl http://localhost:8000/health

# Health check with database
curl http://localhost:8000/health/db
```

**Get All Document IDs:**

```bash
curl http://localhost:8000/documents
```

Expected response:

```json
{
  "document_ids": [1, 2, 3, 4, 5, 6],
  "count": 6
}
```

**Create Document:**

```bash
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test SOAP Note",
    "content": "Subjective: Patient reports fever and cough for 3 days. Objective: Temp 101.2F, HR 88, BP 120/80. Assessment: Likely viral URI. Plan: Rest, fluids, acetaminophen PRN."
  }'
```

Expected response: `201 Created` with document details

**Get Document by ID:**

```bash
curl http://localhost:8000/documents/1
```

**Get All Documents (with pagination):**

```bash
curl "http://localhost:8000/documents/list/all?skip=0&limit=10"
```

**Delete Document:**

```bash
curl -X DELETE http://localhost:8000/documents/1
```

Expected response: `204 No Content`

**Summarize Medical Note:**

```bash
curl -X POST http://localhost:8000/llm/summarize_note \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Subjective: Patient reports fever and cough for 3 days. Objective: Temp 101.2F, HR 88, BP 120/80. Assessment: Likely viral URI. Plan: Rest, fluids, acetaminophen PRN."
  }'
```

Expected response: `200 OK` with summary and token usage

### Using Swagger UI

Navigate to http://localhost:8000/docs for interactive API testing with automatic documentation.

## Development

### Code Quality

- Use type hints throughout
- Follow PEP 8 style guide
- Add docstrings to functions
- Keep routes minimal (delegate to services)

### Adding New Endpoints

1. Define Pydantic schemas in `app/schemas/`
2. Create database models in `app/models/`
3. Add CRUD operations in `app/crud/`
4. Implement business logic in `app/services/`
5. Create route handlers in `app/api/routes/`

## Environment Variables

| Variable               | Description                   | Default                                                        | Required |
| ---------------------- | ----------------------------- | -------------------------------------------------------------- | -------- |
| `DATABASE_URL`         | PostgreSQL connection string  | `postgresql://dfuser:dfpassword@localhost:5432/df_healthbench` | Yes      |
| `API_TITLE`            | API title for docs            | `DF HealthBench API`                                           | No       |
| `API_VERSION`          | API version                   | `1.0.0`                                                        | No       |
| `API_DESCRIPTION`      | API description               | `AI-powered medical document processing API`                   | No       |
| `ENVIRONMENT`          | Environment mode              | `development`                                                  | No       |
| `OPENAI_API_KEY`       | OpenAI API key                | -                                                              | Yes      |
| `OPENAI_API_PROJECT`   | OpenAI project ID             | -                                                              | No       |
| `OPENAI_DEFAULT_MODEL` | Default LLM model             | `gpt-5-nano`                                                   | No       |
| `OPENAI_TEMPERATURE`   | LLM temperature (0.0-2.0)     | `1.0`                                                          | No       |
| `OPENAI_TIMEOUT`       | API request timeout (seconds) | `30`                                                           | No       |

## Quick Start Guide

### 1. Start Database

```bash
# From project root
make db-start
```

### 2. Install Dependencies

```bash
# From backend directory
cd backend
poetry install
```

### 3. Run Application

```bash
# From backend directory
poetry run uvicorn app.main:app --reload
```

### 4. Test the API

```bash
# In a new terminal
curl http://localhost:8000/health
curl http://localhost:8000/documents
```

### 5. View API Documentation

Open http://localhost:8000/docs in your browser

## Troubleshooting

**Database connection failed:**

- Ensure PostgreSQL is running: `make db-start`
- Check `.env` file has correct `DATABASE_URL`
- Verify database logs: `make db-logs`

**Application won't start:**

- Check Poetry environment: `poetry env info`
- Reinstall dependencies: `poetry install`
- Check Python version: `python --version` (should be 3.11+)

**Seeding fails:**

- Ensure `../soap/` directory exists with SOAP note files
- Check file permissions
- Run manual seed: `poetry run python -m app.seed --force`

## Project Status

### ✅ Completed Features

- [x] Part 1: Backend Foundation

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

- [x] Part 2: LLM API Integration
  - [x] OpenAI SDK integration
  - [x] LLM service layer with error handling
  - [x] Medical note summarization endpoint
  - [x] Token usage tracking
  - [x] Request/response logging

### 🚧 Next Steps

- [ ] Part 3: RAG Pipeline
- [ ] Part 4: Agent for Data Extraction
- [ ] Part 5: FHIR Conversion
- [ ] Part 6: Containerization

## License

Private - DF Project
