"""
CRUD package - Database operations.

This package contains all CRUD (Create, Read, Update, Delete)
operations for database models.
"""

from app.crud import document, embedding, document_summary

__all__ = ["document", "embedding", "document_summary"]

