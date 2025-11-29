"""
Configuration module for DF HealthBench API.

This module uses Pydantic Settings to load and validate configuration
from environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
import logging
import os

# Configure logging immediately so config logs appear
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = "postgresql://dfuser:dfpassword@localhost:5432/df_healthbench"
    
    # API Configuration
    api_title: str = "DF HealthBench API"
    api_version: str = "1.0.0"
    api_description: str = "AI-powered medical document processing API"
    
    # Environment
    environment: Literal["development", "production", "test"] = "development"
    
    # OpenAI Configuration
    openai_api_key: str
    openai_api_project: str | None = None
    openai_default_model: str = "gpt-5-nano"
    openai_temperature: float = 1
    openai_timeout: int = 30  # seconds
    
    # OpenAI Embedding Configuration
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536  # text-embedding-3-small dimensions
    
    # RAG Configuration
    chunk_size: int = 800  # Target chunk size in characters
    chunk_overlap: int = 50  # Overlap between chunks for context
    rag_top_k: int = 3  # Number of chunks to retrieve for RAG
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

# IMPORTANT: Explicitly unset OPENAI_PROJECT to prevent OpenAI SDK from auto-detecting it to avoid "mismatched_project" errors
if 'OPENAI_PROJECT' in os.environ:
    logger.warning(f"Removing OPENAI_PROJECT from environment to avoid mismatched_project error")
    del os.environ['OPENAI_PROJECT']

if 'OPENAI_API_PROJECT' in os.environ:
    logger.warning(f"Removing OPENAI_API_PROJECT from environment to avoid mismatched_project error")
    del os.environ['OPENAI_API_PROJECT']

# Debug logging for OpenAI configuration
logger.info("=" * 60)
logger.info("OpenAI Configuration Loaded:")
logger.info(f"  API Key: {'*' * 8}{settings.openai_api_key[-4:] if settings.openai_api_key else 'NOT SET'}")
logger.info(f"  Project ID: {settings.openai_api_project if settings.openai_api_project else 'NOT SET (Optional)'}")
logger.info(f"  Project ID in ENV: {'REMOVED' if 'OPENAI_PROJECT' not in os.environ else 'STILL SET'}")
logger.info(f"  Default Model: {settings.openai_default_model}")
logger.info(f"  Temperature: {settings.openai_temperature}")
logger.info(f"  Timeout: {settings.openai_timeout}s")
logger.info(f"  Embedding Model: {settings.openai_embedding_model}")
logger.info(f"  Embedding Dimension: {settings.embedding_dimension}")
logger.info("=" * 60)
logger.info("RAG Configuration:")
logger.info(f"  Chunk Size: {settings.chunk_size} chars")
logger.info(f"  Chunk Overlap: {settings.chunk_overlap} chars")
logger.info(f"  Top-K Retrieval: {settings.rag_top_k}")
logger.info("=" * 60)

