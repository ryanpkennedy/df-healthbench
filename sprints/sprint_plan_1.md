# Sprint Plan 1: FastAPI Backend Foundation

**Target Duration:** 2 hours  
**Tech Stack:** FastAPI, PostgreSQL, SQLAlchemy, Pydantic, Poetry

---

## Phase 1: Project Initialization (15 minutes)

### 1.1 Initialize Poetry Project

- [ ] Create `pyproject.toml` with Poetry
- [ ] Set Python version (3.11 or 3.12)
- [ ] Configure basic project metadata

### 1.2 Add Core Dependencies

- [ ] Add FastAPI
- [ ] Add Uvicorn (ASGI server)
- [ ] Add SQLAlchemy (ORM)
- [ ] Add psycopg2-binary (PostgreSQL adapter)
- [ ] Add Pydantic (for validation/typing)
- [ ] Add python-dotenv (for environment variables)
- [ ] Add alembic (optional, for migrations)

### 1.3 Project Structure Setup

```
df-healthbench/backend/
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
│           ├── health.py    # Minimal endpoint handlers
│           └── documents.py # Minimal endpoint handlers
├── .env                     # Environment variables
├── .env.example             # Example env file
├── pyproject.toml
└── README.md
```

**Architecture Flow:**

```
Route (endpoint) → Service (business logic) → CRUD (DB operations) → Database
```

---

## Phase 2: Database Configuration (20 minutes)

### 2.1 PostgreSQL Setup

- [ ] Create `.env` file with database credentials
  - `DATABASE_URL=postgresql://user:password@localhost:5432/df_db`
- [ ] Document how to set up local Postgres (README)
- [ ] Create database manually or via script

### 2.2 Database Connection Module (`app/database.py`)

- [ ] Create SQLAlchemy engine with connection pooling
- [ ] Create SessionLocal factory for database sessions
- [ ] Create Base class for declarative models
- [ ] Implement `get_db()` dependency for FastAPI

### 2.3 Configuration Module (`app/config.py`)

- [ ] Create Pydantic Settings class
- [ ] Load DATABASE_URL from environment
- [ ] Add other config variables (API_TITLE, VERSION, etc.)

---

## Phase 3: Data Models (20 minutes)

### 3.1 SQLAlchemy Model (`app/models/document.py`)

- [ ] Create `Document` model class
  - `id`: Integer, Primary Key, Auto-increment
  - `title`: String(255), Not Null
  - `content`: Text, Not Null
  - `created_at`: DateTime, default=now()
  - `updated_at`: DateTime, onupdate=now()
- [ ] Add `__repr__` method for debugging

### 3.2 Pydantic Schemas (`app/schemas/document.py`)

- [ ] Create `DocumentBase` schema (shared fields)
  - `title`: str
  - `content`: str
- [ ] Create `DocumentCreate` schema (for POST requests)
  - Inherits from DocumentBase
  - Add field validators (e.g., min length checks)
- [ ] Create `DocumentResponse` schema (for responses)
  - Inherits from DocumentBase
  - Add `id`: int
  - Add `created_at`: datetime
  - Configure `orm_mode = True`
- [ ] Create `DocumentListResponse` schema
  - `documents`: List of document IDs

### 3.3 Initialize Database Tables

- [ ] Create `create_tables()` function in database.py
- [ ] Call on application startup to create tables if they don't exist

---

## Phase 4: CRUD and Service Layers (25 minutes)

### 4.1 CRUD Layer (`app/crud/document.py`)

- [ ] Create `get_document(db, document_id)` function
  - Query single document by ID
  - Return Document model or None
- [ ] Create `get_documents(db, skip, limit)` function
  - Query all documents with pagination
  - Return list of Document models
- [ ] Create `get_document_ids(db)` function
  - Query all document IDs only (optimized)
  - Return list of integers
- [ ] Create `create_document(db, document)` function
  - Accept DocumentCreate schema
  - Create new document in DB
  - Commit and refresh
  - Return created Document model
- [ ] Add proper type hints for all functions
- [ ] Add docstrings explaining each function

### 4.2 Service Layer (`app/services/document.py`)

- [ ] Create `DocumentService` class (or use functions)
- [ ] Implement `get_all_document_ids(db)` method
  - Call CRUD layer
  - Handle any business logic
  - Return list of IDs
- [ ] Implement `create_new_document(db, title, content)` method
  - Validate input (additional checks if needed)
  - Call CRUD layer
  - Handle errors/exceptions
  - Return created document
- [ ] Implement `get_document_by_id(db, document_id)` method
  - Call CRUD layer
  - Raise custom exception if not found
  - Return document
- [ ] Add proper error handling and logging
- [ ] Keep services focused on business logic, not HTTP concerns

**Note:** For Part 1, services will be simple pass-throughs to CRUD. In later parts, they'll contain more complex logic (LLM calls, data transformation, etc.)

---

## Phase 5: FastAPI Application Setup (15 minutes)

### 5.1 Main Application (`app/main.py`)

- [ ] Initialize FastAPI app with metadata
  - title="DF HealthBench API"
  - version="1.0.0"
  - description
- [ ] Add startup event handler
  - Create database tables on startup
  - Log startup message
- [ ] Add shutdown event handler (close connections)
- [ ] Include API routers

### 5.2 CORS and Middleware (Optional)

- [ ] Add CORS middleware if needed for local testing
- [ ] Add request logging middleware (optional)

---

## Phase 6: API Endpoints - Health Check (10 minutes)

### 6.1 Health Endpoint (`app/api/routes/health.py`)

- [ ] Create `GET /health` endpoint
  - Return `{"status": "ok"}`
- [ ] Add database connectivity check (optional)
  - Try a simple query
  - Return `{"status": "ok", "database": "connected"}`
- [ ] Add proper error handling

### 6.2 Router Registration

- [ ] Include health router in main.py
- [ ] Test endpoint manually

---

## Phase 7: API Endpoints - Documents (25 minutes)

### 7.1 GET /documents Endpoint

- [ ] Create `GET /documents` in `app/api/routes/documents.py`
- [ ] Inject database session dependency (`Depends(get_db)`)
- [ ] Call `DocumentService.get_all_document_ids(db)`
- [ ] Return list of document IDs only (as per spec)
- [ ] Add error handling with try-except
- [ ] Return appropriate HTTP status codes (200 OK)
- [ ] **Keep endpoint minimal** - only handle HTTP concerns

### 7.2 POST /documents Endpoint

- [ ] Create `POST /documents` endpoint
- [ ] Accept JSON body with `title` and `content`
- [ ] Use `DocumentCreate` Pydantic schema for validation
- [ ] Inject database session dependency
- [ ] Call `DocumentService.create_new_document(db, title, content)`
- [ ] Return created document with ID using `DocumentResponse` schema
- [ ] Add error handling:
  - Missing fields (422 - handled by Pydantic automatically)
  - Database errors (500 Internal Server Error)
  - Duplicate titles (optional constraint)
- [ ] Return 201 Created status code
- [ ] **Keep endpoint minimal** - delegate logic to service layer

### 7.3 GET /documents/{id} Endpoint (Stretch)

- [ ] Create endpoint to fetch single document by ID
- [ ] Inject database session dependency
- [ ] Call `DocumentService.get_document_by_id(db, id)`
- [ ] Return 404 if document not found (handle in service)
- [ ] Return full document details with `DocumentResponse` schema
- [ ] **Keep endpoint minimal** - service handles the logic

---

## Phase 8: Seed Data (10 minutes)

### 8.1 Create Seed Script

- [ ] Create `seed_db.py` or function in main.py
- [ ] Load SOAP notes from `soap/` directory
- [ ] Insert each SOAP note as a document
  - title: filename (e.g., "soap_01")
  - content: file contents
- [ ] Add option to run on startup or via CLI

### 8.2 Test Data Verification

- [ ] Verify 6 SOAP documents are loaded
- [ ] Check via GET /documents endpoint

---

## Phase 9: Testing & Documentation (10 minutes)

### 9.1 Manual Testing

- [ ] Start server: `poetry run uvicorn app.main:app --reload`
- [ ] Test GET /health → Should return 200 OK
- [ ] Test GET /documents → Should return list of IDs
- [ ] Test POST /documents with valid data → Should return 201 Created
- [ ] Test POST /documents with missing field → Should return 422
- [ ] Test POST /documents with empty content → Should return 422

### 9.2 Documentation

- [ ] Update README.md with:
  - Prerequisites (Python, Poetry, PostgreSQL)
  - Setup instructions
  - Database setup commands
  - How to run the application
  - API endpoint documentation
  - Example curl commands
  - Architecture overview (Route → Service → CRUD → DB)
- [ ] Add docstrings to key functions
- [ ] Document environment variables in .env.example

### 9.3 Interactive API Docs

- [ ] Verify Swagger UI at `http://localhost:8000/docs`
- [ ] Verify ReDoc at `http://localhost:8000/redoc`
- [ ] Test all endpoints through Swagger UI

---

## Success Criteria

✅ **Core Requirements:**

- [ ] FastAPI application runs successfully
- [ ] GET /health returns 200 with status confirmation
- [ ] PostgreSQL database is connected and accessible
- [ ] Documents table exists with proper schema
- [ ] GET /documents returns list of document IDs
- [ ] POST /documents creates new documents with validation
- [ ] Error handling works for missing/invalid data
- [ ] SOAP notes are loaded as seed data

✅ **Code Quality:**

- [ ] Proper separation of concerns (models, schemas, routes)
- [ ] Type hints used throughout
- [ ] Pydantic models for validation
- [ ] SQLAlchemy ORM properly configured
- [ ] Environment variables for configuration

✅ **Documentation:**

- [ ] README with clear setup instructions
- [ ] .env.example file provided
- [ ] API endpoints documented
- [ ] Code has docstrings

---

## Time Allocation Summary

| Phase     | Task                   | Estimated Time         |
| --------- | ---------------------- | ---------------------- |
| 1         | Project Initialization | 15 min                 |
| 2         | Database Configuration | 20 min                 |
| 3         | Data Models            | 20 min                 |
| 4         | CRUD & Service Layers  | 25 min                 |
| 5         | FastAPI Setup          | 15 min                 |
| 6         | Health Endpoint        | 10 min                 |
| 7         | Documents Endpoints    | 25 min                 |
| 8         | Seed Data              | 10 min                 |
| 9         | Testing & Docs         | 10 min                 |
| **Total** |                        | **150 min (2h 30min)** |

_Note: Time estimates include buffer for debugging and adjustments. The additional 30 minutes (compared to 2hr target) accounts for the CRUD/Service layer architecture, which will save significant time in Parts 2-5._

---

## Architecture Benefits

**Why CRUD + Service layers?**

- **Separation of Concerns:** Routes handle HTTP, services handle logic, CRUD handles DB
- **Testability:** Easy to unit test business logic without HTTP context
- **Reusability:** Service methods can be called from multiple routes
- **Maintainability:** Changes to DB queries don't affect business logic
- **Scalability:** Ready for complex logic in Parts 2-5 (LLM calls, RAG, agents)

**Example Flow:**

```python
# Route (minimal)
@router.get("/documents")
def get_documents(db: Session = Depends(get_db)):
    return document_service.get_all_document_ids(db)

# Service (business logic)
def get_all_document_ids(db: Session):
    return document_crud.get_document_ids(db)

# CRUD (database operations)
def get_document_ids(db: Session):
    return db.query(Document.id).all()
```

---

## Notes & Reminders

- **Database URL Format:** `postgresql://username:password@host:port/database_name`
- **Keep it simple:** Focus on core functionality, avoid over-engineering
- **Error handling:** Add basic try-catch blocks for database operations
- **Validation:** Use Pydantic's built-in validators for field validation
- **Testing:** Manual testing via Swagger UI is sufficient for Part 1
- **OpenAI API:** Not needed for Part 1, will be used in Part 2

---

## Next Steps (Part 2 Preview)

After completing Part 1, Part 2 will involve:

- Adding OpenAI API integration
- Creating POST /summarize_note endpoint
- Implementing LLM-based document summarization
