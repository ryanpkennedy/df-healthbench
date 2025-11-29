"""
API Routes package.

This package contains all API endpoint route handlers.
"""

from app.api.routes import health, documents, llm, rag, extraction

__all__ = ["health", "documents", "llm", "rag", "extraction"]

