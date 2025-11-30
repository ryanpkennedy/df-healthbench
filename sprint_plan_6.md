# Sprint Plan 6: Containerization and Docker Compose Deployment

**Estimated Time:** 1 hour  
**Goal:** Containerize the FastAPI backend and integrate with existing docker-compose setup for production-ready deployment

---

## Overview

This sprint implements Part 6 of the project: containerizing the entire application using Docker and Docker Compose for easy deployment.

**What We're Building:**

- Dockerfile for the FastAPI backend application
- Updated docker-compose.yml with backend service (integrates with existing postgres service)
- Environment variable management for container deployment
- Health checks and service dependencies
- Production-ready configuration

**Current State:**

- ✅ docker-compose.yml exists with PostgreSQL + PGVector service
- ✅ Backend fully functional locally (Parts 1-5 complete)
- ✅ .env.example file exists with configuration template

**Target State:**

- ✅ Single `docker-compose up` command launches entire stack
- ✅ Backend accessible at http://localhost:8000
- ✅ All endpoints working in containerized environment
- ✅ Data persists across container restarts
- ✅ Production-ready with health checks

---

## Phase 1: Create Backend Dockerfile (15 minutes)

### 1.1 Create Multi-Stage Dockerfile

**File:** `backend/Dockerfile`

**Purpose:** Efficient, production-ready Docker image for FastAPI backend

**Key Requirements:**

- Use multi-stage build (builder + runtime stages)
- Base image: `python:3.11-slim` (lightweight, official)
- Install Poetry and dependencies in builder stage
- Copy only necessary files to runtime stage
- Non-root user for security
- Health check instruction

**Structure:**

```dockerfile
# Stage 1: Builder (install dependencies)
FROM python:3.11-slim as builder
- Install Poetry
- Copy pyproject.toml and poetry.lock
- Install dependencies to virtual environment
- No dev dependencies

# Stage 2: Runtime (run application)
FROM python:3.11-slim
- Copy virtual environment from builder
- Copy application code
- Create non-root user
- Set working directory
- Expose port 8000
- Health check
- CMD: uvicorn with production settings
```

**Key Decisions:**

- Python 3.11-slim (balance of compatibility and size)
- Multi-stage for smaller final image (~200MB vs ~800MB)
- Poetry for dependency management (consistent with local dev)
- Uvicorn with 4 workers for production
- Non-root user for security best practice

**Estimated time:** 10 minutes

---

### 1.2 Create .dockerignore File

**File:** `backend/.dockerignore`

**Purpose:** Exclude unnecessary files from Docker context

**Contents:**

- `__pycache__/`
- `*.pyc`
- `.pytest_cache/`
- `.env` (use docker-compose env instead)
- `notebooks/`
- `*.ipynb`
- `.venv/`
- `.git/`

**Estimated time:** 2 minutes

---

### 1.3 Test Dockerfile Build

**Verify image builds successfully:**

```bash
cd backend
docker build -t df-healthbench-backend:latest .
```

**Check image size:**

```bash
docker images df-healthbench-backend
```

**Expected:** ~200-300MB with multi-stage build

**Estimated time:** 3 minutes

---

## Phase 2: Update Docker Compose Configuration (15 minutes)

### 2.1 Add Backend Service to docker-compose.yml

**File:** `docker-compose.yml` (root directory)

**Add backend service:**

```yaml
services:
  postgres:
    # ... existing config ...

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: df-healthbench-backend
    ports:
      - '8000:8000'
    environment:
      DATABASE_URL: postgresql://dfuser:dfpassword@postgres:5432/df_healthbench
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      OPENAI_DEFAULT_MODEL: ${OPENAI_DEFAULT_MODEL:-gpt-4o-mini}
      OPENAI_TEMPERATURE: ${OPENAI_TEMPERATURE:-1.0}
      API_TITLE: 'DF HealthBench API'
      API_VERSION: '1.0.0'
      ENVIRONMENT: 'production'
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ../med_docs:/app/med_docs:ro
    healthcheck:
      test: ['CMD', 'curl', '-f', 'http://localhost:8000/health']
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
```

**Key Features:**

- `depends_on` with health check condition (waits for DB to be ready)
- Environment variables from host .env file
- Volume mount for med_docs (read-only, for seeding)
- Health check using curl
- Restart policy for resilience

**Estimated time:** 8 minutes

---

### 2.2 Update Network Configuration (if needed)

**Add explicit network (optional but recommended):**

```yaml
networks:
  df-network:
    driver: bridge

services:
  postgres:
    networks:
      - df-network

  backend:
    networks:
      - df-network
```

**Estimated time:** 2 minutes

---

### 2.3 Test Docker Compose Build

**Build services:**

```bash
docker-compose build
```

**Verify images created:**

```bash
docker images | grep df-healthbench
```

**Estimated time:** 5 minutes

---

## Phase 3: Environment Variable Management (10 minutes)

### 3.1 Create Root-Level .env File

**File:** `.env` (root directory, for docker-compose)

**Purpose:** Centralized environment configuration for containerized deployment

**Contents:**

```bash
# OpenAI Configuration (Required)
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_DEFAULT_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=1.0
OPENAI_TIMEOUT=30

# Optional: OpenAI Project ID
# OPENAI_API_PROJECT=proj-your-project-id
```

**Notes:**

- Database config is hardcoded in docker-compose (internal networking)
- Only external secrets (OpenAI) need to be in .env
- Backend/.env is for local development only

**Estimated time:** 3 minutes

---

### 3.2 Create Root-Level .env.example

**File:** `.env.example` (root directory)

**Purpose:** Template for users to create their own .env file

**Contents:**

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-proj-replace-with-your-actual-key
OPENAI_DEFAULT_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=1.0
OPENAI_TIMEOUT=30
```

**Estimated time:** 2 minutes

---

### 3.3 Update .gitignore

**File:** `.gitignore` (root directory)

**Add:**

```
.env
backend/.env
```

**Verify .env.example is NOT ignored**

**Estimated time:** 1 minute

---

### 3.4 Document Environment Setup in README

**Quick note in root README.md:**

````markdown
## Quick Start with Docker

1. Create `.env` file from template:
   ```bash
   cp .env.example .env
   ```
````

2. Add your OpenAI API key to `.env`

3. Start all services:

   ```bash
   docker-compose up -d
   ```

4. Access the API:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

````

**Estimated time:** 4 minutes

---

## Phase 4: Testing & Verification (15 minutes)

### 4.1 Full Stack Startup Test

**Start services:**

```bash
docker-compose up -d
````

**Watch logs:**

```bash
docker-compose logs -f backend
```

**Verify:**

- ✅ PostgreSQL starts and initializes PGVector
- ✅ Backend waits for database health check
- ✅ Backend connects to database successfully
- ✅ Database tables created
- ✅ SOAP notes seeded automatically
- ✅ Embeddings generated automatically
- ✅ Backend health check passes

**Estimated time:** 5 minutes

---

### 4.2 Endpoint Testing

**Test each endpoint category:**

```bash
# Health check
curl http://localhost:8000/health

# Documents
curl http://localhost:8000/documents

# LLM (requires OpenAI key)
curl -X POST http://localhost:8000/llm/summarize_document/1

# RAG
curl http://localhost:8000/rag/stats

curl -X POST http://localhost:8000/rag/answer_question \
  -H "Content-Type: application/json" \
  -d '{"question": "What medications are mentioned?"}'

# Agent extraction (test with SOAP note)
curl -X POST http://localhost:8000/agent/extract_structured \
  -H "Content-Type: application/json" \
  -d '{"text": "Subjective: 45yo male with Type 2 Diabetes..."}'

# FHIR conversion (use extraction output)
# Test via Swagger UI: http://localhost:8000/docs
```

**Verify:**

- ✅ All endpoints return expected responses
- ✅ Database queries work
- ✅ OpenAI API calls work
- ✅ External API calls work (NLM for ICD/RxNorm)
- ✅ No permission errors

**Estimated time:** 7 minutes

---

### 4.3 Container Management Test

**Test restart behavior:**

```bash
# Stop services
docker-compose down

# Restart services
docker-compose up -d

# Verify data persists (documents still exist)
curl http://localhost:8000/documents
```

**Test individual service restart:**

```bash
docker-compose restart backend
```

**Check logs for errors:**

```bash
docker-compose logs backend | grep -i error
docker-compose logs postgres | grep -i error
```

**Estimated time:** 3 minutes

---

## Phase 5: Documentation & Finalization (5 minutes)

### 5.1 Update Root README.md

**Add Docker Deployment section:**

````markdown
## Deployment with Docker

### Quick Start

```bash
# 1. Create environment file
cp .env.example .env

# 2. Add your OpenAI API key to .env
nano .env

# 3. Start all services
docker-compose up -d

# 4. View logs
docker-compose logs -f

# 5. Access API
# - API: http://localhost:8000
# - Interactive docs: http://localhost:8000/docs
```
````

### Docker Commands

```bash
# Start services (detached)
docker-compose up -d

# View logs
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f postgres

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Clean restart (destroys data)
docker-compose down -v
docker-compose up -d --build
```

### Testing Endpoints

After starting services, test the API:

```bash
# Health check
curl http://localhost:8000/health

# List documents
curl http://localhost:8000/documents

# Interactive testing
open http://localhost:8000/docs
```

````

**Estimated time:** 3 minutes

---

### 5.2 Update backend/README.md

**Add Docker section:**

```markdown
## Running with Docker

See root-level README.md for Docker Compose instructions.

The backend runs on port 8000 inside the container and is exposed on the host.
````

**Estimated time:** 1 minute

---

### 5.3 Mark Part 6 Complete

**Update backend/README.md Project Status:**

```markdown
**Part 6: Containerization**

- [x] Multi-stage Dockerfile for backend
- [x] Docker Compose configuration with all services
- [x] Environment variable management (.env, .env.example)
- [x] Service health checks and dependencies
- [x] Volume mounts for data persistence
- [x] Production-ready configuration
- [x] Documentation with deployment instructions
- [x] Tested full stack deployment
```

**Estimated time:** 1 minute

---

## Implementation Order

**Recommended sequence:**

1. **Dockerfile Creation** (Phase 1)

   - Write backend/Dockerfile
   - Create .dockerignore
   - Test build locally

2. **Docker Compose Update** (Phase 2)

   - Add backend service to docker-compose.yml
   - Configure dependencies and health checks
   - Test build with docker-compose

3. **Environment Setup** (Phase 3)

   - Create root .env.example
   - Update .gitignore
   - Document environment variables

4. **Full Stack Testing** (Phase 4)

   - Start all services with docker-compose up
   - Test all endpoints
   - Verify data persistence
   - Check logs for errors

5. **Documentation** (Phase 5)
   - Update root README.md
   - Update backend README.md
   - Mark project complete

---

## Success Criteria

- [ ] Multi-stage Dockerfile builds successfully (~200-300MB)
- [ ] docker-compose.yml includes backend service with proper configuration
- [ ] Backend service depends on postgres health check
- [ ] All services start with single `docker-compose up` command
- [ ] Backend accessible at http://localhost:8000
- [ ] All endpoints tested and working in containers
- [ ] Environment variables properly configured
- [ ] Data persists across container restarts (postgres volume)
- [ ] Health checks working for both services
- [ ] Logs show successful startup and seeding
- [ ] Documentation updated with deployment instructions
- [ ] No hardcoded secrets in docker-compose.yml or Dockerfile

---

## Time Allocation Summary

| Phase                       | Time       |
| --------------------------- | ---------- |
| Phase 1: Dockerfile         | 15 min     |
| Phase 2: Docker Compose     | 15 min     |
| Phase 3: Environment Config | 10 min     |
| Phase 4: Testing            | 15 min     |
| Phase 5: Documentation      | 5 min      |
| **Total**                   | **1 hour** |

---

## Key Design Decisions

### Why Multi-Stage Dockerfile?

- ✅ Smaller final image (excludes build tools, Poetry, etc.)
- ✅ Faster deployment (less data to transfer)
- ✅ More secure (fewer packages in production image)
- ✅ Industry best practice

### Why python:3.11-slim?

- ✅ Balance of size and compatibility
- ✅ Official Python image (trusted, maintained)
- ✅ Includes necessary system libraries
- ✅ Compatible with all dependencies

### Why Service Health Checks?

- ✅ Ensures proper startup order (DB before backend)
- ✅ Enables automatic restart on failure
- ✅ Better monitoring and orchestration
- ✅ Required for production deployments

### Why Volume Mount for med_docs?

- ✅ No need to rebuild image when documents change
- ✅ Easy to swap document sets for testing
- ✅ Read-only mount for security
- ✅ Supports local development workflow

### Environment Variable Strategy

**Root .env:**

- External secrets (OpenAI key)
- Deployment-specific config
- Used by docker-compose

**backend/.env:**

- Local development only
- Not used in containers
- DATABASE_URL points to localhost

**docker-compose.yml:**

- Internal config (database connection using service name)
- Non-secret defaults
- Reads from root .env for secrets

---

## Potential Challenges & Mitigations

| Challenge                            | Mitigation                                               |
| ------------------------------------ | -------------------------------------------------------- |
| Backend starts before DB is ready    | Use `depends_on` with health check condition             |
| Large Docker image size              | Multi-stage build, exclude unnecessary files             |
| Environment variables not working    | Test with `docker-compose config` to verify substitution |
| SOAP notes not found for seeding     | Volume mount ../med_docs directory                       |
| OpenAI API key not accessible        | Use .env file at root, reference in docker-compose       |
| Permission errors with volumes       | Use non-root user in Dockerfile, proper volume ownership |
| Slow startup (embeddings generation) | Expected on first run, logs show progress                |
| Port 8000 already in use             | Stop local dev server first, or change port mapping      |

---

## Testing Strategy

### Build Testing

1. Build Dockerfile independently: `docker build -t df-healthbench-backend ./backend`
2. Check image size: `docker images df-healthbench-backend`
3. Build with docker-compose: `docker-compose build`

### Startup Testing

1. Start services: `docker-compose up -d`
2. Monitor logs: `docker-compose logs -f`
3. Check service status: `docker-compose ps`
4. Verify health checks: `docker inspect df-healthbench-backend | grep -A 10 Health`

### Endpoint Testing

1. Health check: `curl http://localhost:8000/health`
2. Database connectivity: `curl http://localhost:8000/health/db`
3. Documents: `curl http://localhost:8000/documents`
4. LLM: Test via Swagger UI (http://localhost:8000/docs)
5. RAG: `curl http://localhost:8000/rag/stats`
6. Agent: Test extraction endpoint with sample SOAP note
7. FHIR: Test conversion endpoint via Swagger UI

### Persistence Testing

1. Create a test document via API
2. Stop services: `docker-compose down`
3. Start services: `docker-compose up -d`
4. Verify document still exists: `curl http://localhost:8000/documents`

### Performance Testing

1. Check container resource usage: `docker stats`
2. Monitor startup time (should be <60s including seeding)
3. Test concurrent requests (Swagger UI "Try it out" multiple times)

---

## Docker Compose Configuration Details

### Service Dependencies

```
backend depends_on postgres (with health check)
↓
backend waits for postgres health check to pass
↓
backend starts and connects to database
↓
backend runs migrations and seeding
↓
backend health check passes
↓
System ready
```

### Port Mappings

- `5432:5432` - PostgreSQL (host:container)
- `8000:8000` - FastAPI backend (host:container)

### Volume Mounts

- `postgres_data:/var/lib/postgresql/data` - Database persistence (named volume)
- `./backend/init_pgvector.sql:/docker-entrypoint-initdb.d/` - DB initialization
- `../med_docs:/app/med_docs:ro` - SOAP notes for seeding (read-only)

### Networks

- Default bridge network or explicit `df-network`
- Services communicate using service names (e.g., `postgres:5432`)

---

## Dockerfile Configuration Details

### Multi-Stage Build Structure

**Stage 1: Builder**

- Install Poetry
- Copy dependency files (pyproject.toml, poetry.lock)
- Install dependencies to virtual environment
- Export requirements.txt (alternative approach)

**Stage 2: Runtime**

- Copy virtual environment from builder
- Copy application code
- Create non-root user (dfuser)
- Set working directory (/app)
- Expose port 8000
- Health check instruction
- CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`

### Security Considerations

- Non-root user for application process
- Read-only volume mounts where possible
- Secrets via environment variables (not in image)
- Minimal base image (fewer attack vectors)
- Health checks for monitoring

### Production Settings

- 4 Uvicorn workers (CPU-based parallelism)
- Bind to 0.0.0.0 (accessible from outside container)
- Port 8000 (standard)
- No --reload (production mode)
- Logs to stdout (Docker best practice)

---

## Post-Deployment Verification Checklist

After `docker-compose up -d`:

- [ ] Check service status: `docker-compose ps` (all services should be "Up" and "healthy")
- [ ] Check logs: `docker-compose logs backend | tail -50` (no errors)
- [ ] Check database logs: `docker-compose logs postgres | tail -50` (PGVector enabled)
- [ ] Test health endpoint: `curl http://localhost:8000/health` (returns `{"status":"ok"}`)
- [ ] Test database health: `curl http://localhost:8000/health/db` (database connected)
- [ ] Check documents seeded: `curl http://localhost:8000/documents` (returns 6 documents)
- [ ] Check embeddings generated: `curl http://localhost:8000/rag/stats` (45+ chunks)
- [ ] Test LLM endpoint: Via Swagger UI (http://localhost:8000/docs)
- [ ] Test RAG endpoint: `curl -X POST http://localhost:8000/rag/answer_question -H "Content-Type: application/json" -d '{"question":"What medications are mentioned?"}'`
- [ ] Check resource usage: `docker stats` (CPU, memory reasonable)
- [ ] Test restart: `docker-compose restart backend` (recovers successfully)
- [ ] Test data persistence: Create doc, restart, verify doc exists

---

## Troubleshooting Guide

### Issue: Backend fails to start

**Check:**

- Database health check status: `docker-compose ps postgres`
- Backend logs: `docker-compose logs backend`
- Database connection string in docker-compose.yml

**Solution:**

- Wait for postgres health check to pass (can take 30-60s)
- Verify DATABASE_URL uses service name `postgres` not `localhost`

### Issue: OpenAI API calls fail

**Check:**

- .env file exists at root level
- OPENAI_API_KEY is set correctly
- Environment variables loaded: `docker-compose config | grep OPENAI`

**Solution:**

- Copy .env.example to .env
- Add valid OpenAI API key
- Restart services: `docker-compose restart backend`

### Issue: SOAP notes not seeded

**Check:**

- Volume mount configuration in docker-compose.yml
- med_docs directory exists at ../med_docs relative to docker-compose.yml
- Seeding logs: `docker-compose logs backend | grep -i seed`

**Solution:**

- Verify med_docs directory path
- Check volume mount syntax in docker-compose.yml
- Manual seed: `docker-compose exec backend python -m app.seed --force`

### Issue: Port 8000 already in use

**Check:**

- Local development server running
- Other containers using port 8000: `docker ps | grep 8000`

**Solution:**

- Stop local dev server: `pkill -f uvicorn`
- Change port mapping in docker-compose.yml: `"8001:8000"`

### Issue: Docker build fails

**Check:**

- Docker context includes necessary files
- .dockerignore not excluding required files
- Poetry dependencies resolve correctly

**Solution:**

- Check Dockerfile syntax
- Test Poetry install locally first
- Clear Docker cache: `docker-compose build --no-cache`

---

## Files to Create/Modify

### New Files

1. `backend/Dockerfile` - Multi-stage Dockerfile for backend
2. `backend/.dockerignore` - Exclude files from Docker context
3. `.env.example` - Template for environment variables (root level)

### Modified Files

1. `docker-compose.yml` - Add backend service
2. `README.md` - Add Docker deployment instructions (root level)
3. `backend/README.md` - Update with Docker section and mark Part 6 complete
4. `.gitignore` - Ensure .env is ignored (if not already)

### Files to Create (by user)

1. `.env` - User creates from .env.example with actual OpenAI key

---

## Next Steps After Completion

**Project is complete! All 6 parts implemented.**

**Optional enhancements:**

- Add Makefile commands for Docker operations
- Add docker-compose.prod.yml for production-specific config
- Add CI/CD pipeline (GitHub Actions)
- Add monitoring (Prometheus, Grafana)
- Add log aggregation (ELK stack)
- Add SSL/TLS termination (nginx reverse proxy)
- Deploy to cloud (AWS ECS, GCP Cloud Run, Azure Container Instances)

---

## References

- **Docker Best Practices:** https://docs.docker.com/develop/dev-best-practices/
- **Docker Compose Docs:** https://docs.docker.com/compose/
- **Multi-Stage Builds:** https://docs.docker.com/build/building/multi-stage/
- **FastAPI in Docker:** https://fastapi.tiangolo.com/deployment/docker/
- **Poetry with Docker:** https://github.com/python-poetry/poetry/discussions/1879

---

**Ready to implement! 🚀**
