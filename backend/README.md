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
- PostgreSQL (local or Docker)

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

### 3. Set up PostgreSQL

**Option A: Local PostgreSQL**

```bash
# Install PostgreSQL (macOS)
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb df_db
```

**Option B: Docker PostgreSQL**

```bash
docker run --name df-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=df_db \
  -p 5432:5432 \
  -d postgres:15
```

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your configuration
# Update DATABASE_URL if needed
```

## Running the Application

### Development Server

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access the API

- **API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## API Endpoints

### Part 1: Backend Foundation

- `GET /health` - Health check endpoint
- `GET /documents` - List all document IDs
- `POST /documents` - Create a new document
- `GET /documents/{id}` - Get document by ID (stretch goal)

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection setup
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
│           ├── health.py    # Health check endpoint
│           └── documents.py # Document endpoints
├── .env                     # Environment variables (not in git)
├── .env.example             # Example environment variables
├── .gitignore
├── pyproject.toml           # Poetry dependencies
└── README.md
```

## Testing

### Manual Testing with curl

**Health Check:**

```bash
curl http://localhost:8000/health
```

**Get All Documents:**

```bash
curl http://localhost:8000/documents
```

**Create Document:**

```bash
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Document",
    "content": "This is test content"
  }'
```

**Get Document by ID:**

```bash
curl http://localhost:8000/documents/1
```

### Using Swagger UI

Navigate to http://localhost:8000/docs for interactive API testing.

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

| Variable         | Description                  | Default                                               |
| ---------------- | ---------------------------- | ----------------------------------------------------- |
| `DATABASE_URL`   | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/df_db` |
| `API_TITLE`      | API title for docs           | `DF HealthBench API`                                  |
| `API_VERSION`    | API version                  | `1.0.0`                                               |
| `OPENAI_API_KEY` | OpenAI API key (Part 2+)     | -                                                     |
| `HOST`           | Server host                  | `0.0.0.0`                                             |
| `PORT`           | Server port                  | `8000`                                                |
| `DEBUG`          | Debug mode                   | `True`                                                |

## Next Steps

- [ ] Complete Part 1: Backend Foundation
- [ ] Part 2: LLM API Integration
- [ ] Part 3: RAG Pipeline
- [ ] Part 4: Agent for Data Extraction
- [ ] Part 5: FHIR Conversion
- [ ] Part 6: Containerization

## License

Private - DF Project
