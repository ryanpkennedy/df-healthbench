"""
Schemas package - Pydantic models for validation.

This package contains all request/response schemas for FastAPI.
"""

from app.schemas.document import (
    DocumentBase,
    DocumentCreate,
    DocumentResponse,
    DocumentListResponse,
)
from app.schemas.llm import (
    SummarizeRequest,
    SummarizeResponse,
    TokenUsage,
    ErrorResponse,
)
from app.schemas.rag import (
    QuestionRequest,
    SourceChunk,
    AnswerResponse,
    EmbedDocumentResponse,
    EmbedAllResponse,
    RAGStatsResponse,
)
from app.schemas.extraction import (
    PatientInfo,
    VitalSigns,
    DiagnosisCode,
    MedicationCode,
    StructuredClinicalData,
    ExtractionRequest,
    ExtractionResponse,
)

__all__ = [
    "DocumentBase",
    "DocumentCreate",
    "DocumentResponse",
    "DocumentListResponse",
    "SummarizeRequest",
    "SummarizeResponse",
    "TokenUsage",
    "ErrorResponse",
    "QuestionRequest",
    "SourceChunk",
    "AnswerResponse",
    "EmbedDocumentResponse",
    "EmbedAllResponse",
    "RAGStatsResponse",
    "PatientInfo",
    "VitalSigns",
    "DiagnosisCode",
    "MedicationCode",
    "StructuredClinicalData",
    "ExtractionRequest",
    "ExtractionResponse",
]

