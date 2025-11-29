"""
DF HealthBench - FastAPI Application Entry Point

This is the main application file that initializes FastAPI and
registers all routes and middleware.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import create_tables, check_db_connection
from app.api.routes import health, documents, llm, rag

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    This replaces the deprecated @app.on_event decorators.
    """
    # Startup
    logger.info("=" * 60)
    logger.info("Starting DF HealthBench API")
    logger.info("=" * 60)
    
    # Check database connection
    logger.info("Checking database connection...")
    if check_db_connection():
        logger.info("✅ Database connection successful")
    else:
        logger.error("❌ Database connection failed")
        raise RuntimeError("Could not connect to database")
    
    # Create tables
    logger.info("Creating database tables...")
    create_tables()
    logger.info("✅ Database tables ready")
    
    # Seed database with SOAP notes (if empty)
    try:
        from app.seed import seed_database
        logger.info("Checking if database needs seeding...")
        # Note: seed_database will automatically generate embeddings if documents are created
        # and no embeddings exist. This happens only on first startup.
        seed_database(force=False, skip_embeddings=False)
    except Exception as e:
        logger.warning(f"Failed to seed database: {e}")
        logger.warning("Application will continue, but you may need to manually seed data")
    
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"API Title: {settings.api_title}")
    logger.info(f"API Version: {settings.api_version}")
    logger.info("=" * 60)
    logger.info("🚀 Application started successfully")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("Shutting down DF HealthBench API")
    logger.info("=" * 60)


# Initialize FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information.
    
    Returns basic information about the API.
    """
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "environment": settings.environment,
        "docs": "/docs",
        "status": "running"
    }


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(llm.router, prefix="/llm", tags=["LLM"])
app.include_router(rag.router, prefix="/rag", tags=["RAG"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

