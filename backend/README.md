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

| Variable          | Description                  | Default                                                        |
| ----------------- | ---------------------------- | -------------------------------------------------------------- |
| `DATABASE_URL`    | PostgreSQL connection string | `postgresql://dfuser:dfpassword@localhost:5432/df_healthbench` |
| `API_TITLE`       | API title for docs           | `DF HealthBench API`                                           |
| `API_VERSION`     | API version                  | `1.0.0`                                                        |
| `API_DESCRIPTION` | API description              | `AI-powered medical document processing API`                   |
| `ENVIRONMENT`     | Environment mode             | `development`                                                  |
| `OPENAI_API_KEY`  | OpenAI API key (Part 2+)     | -                                                              |

## Next Steps

- [ ] Complete Part 1: Backend Foundation
- [ ] Part 2: LLM API Integration
- [ ] Part 3: RAG Pipeline
- [ ] Part 4: Agent for Data Extraction
- [ ] Part 5: FHIR Conversion
- [ ] Part 6: Containerization

## License

Private - DF Project
