"""
RAG (Retrieval-Augmented Generation) endpoints.

Provides endpoints for document embedding, vector search, and question answering
using the RAG pipeline.
"""

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.schemas.rag import (
    QuestionRequest,
    AnswerResponse,
    EmbedDocumentResponse,
    EmbedAllResponse,
    RAGStatsResponse,
    ErrorResponse,
    DocumentEmbeddingResult,
)
from app.services.rag import RAGService, RAGServiceError, NoEmbeddingsFoundError
from app.services.document import DocumentNotFoundError


router = APIRouter()
logger = logging.getLogger(__name__)


# Common response definitions for OpenAPI documentation
COMMON_RAG_RESPONSES = {
    400: {
        "description": "Invalid input (empty question, invalid parameters, etc.)",
        "model": ErrorResponse,
    },
    500: {
        "description": "Internal server error",
        "model": ErrorResponse,
    },
    503: {
        "description": "Service unavailable (OpenAI API error)",
        "model": ErrorResponse,
    },
}


@router.post(
    "/answer_question",
    response_model=AnswerResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **COMMON_RAG_RESPONSES,
        503: {
            "description": "No embeddings found - documents need to be embedded first",
            "model": ErrorResponse,
        }
    },
    summary="Answer a question using RAG",
    description="""
    Answer a question using the RAG (Retrieval-Augmented Generation) pipeline.
    
    This endpoint:
    1. Generates an embedding for your question
    2. Searches for similar document chunks using vector similarity
    3. Builds context from the most relevant chunks
    4. Uses an LLM to generate an answer based on the context
    5. Returns the answer with source citations
    
    **Note:** Documents must be embedded first using `/rag/embed_all` or `/rag/embed_document/{id}`.
    """
)
async def answer_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
) -> AnswerResponse:
    """
    Answer a question using the RAG pipeline.
    
    Args:
        request: Question and optional parameters (top_k, similarity_threshold, model)
        db: Database session (injected)
        
    Returns:
        Answer with source citations and metadata
    """
    logger.info(
        f"Received RAG question: '{request.question[:100]}...' "
        f"(top_k={request.top_k}, threshold={request.similarity_threshold})"
    )
    
    try:
        rag_service = RAGService(db)
        
        result = rag_service.answer_question(
            question=request.question,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            model=request.model
        )
        
        logger.info(
            f"Question answered successfully: "
            f"sources={len(result['sources'])}, "
            f"tokens={result['token_usage']['total_tokens']}, "
            f"time={result['processing_time_ms']}ms"
        )
        
        return AnswerResponse(**result)
        
    except ValueError as e:
        logger.warning(f"Invalid question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except NoEmbeddingsFoundError as e:
        logger.error(f"No embeddings found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
        
    except RAGServiceError as e:
        logger.error(f"RAG service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG service error: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in answer_question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post(
    "/embed_document/{document_id}",
    response_model=EmbedDocumentResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **COMMON_RAG_RESPONSES,
        404: {
            "description": "Document not found",
            "model": ErrorResponse,
        }
    },
    summary="Embed a single document",
    description="""
    Chunk and embed a single document for RAG.
    
    This endpoint:
    1. Retrieves the document from the database
    2. Splits it into semantic chunks
    3. Generates embeddings for each chunk using OpenAI
    4. Stores the embeddings in the database
    
    If the document already has embeddings, it will be skipped unless you use `force=true`.
    """
)
async def embed_document(
    document_id: int,
    force: bool = False,
    db: Session = Depends(get_db)
) -> EmbedDocumentResponse:
    """
    Embed a single document.
    
    Args:
        document_id: ID of the document to embed
        force: If True, re-embed even if embeddings exist
        db: Database session (injected)
        
    Returns:
        Embedding operation results
    """
    logger.info(f"Embedding document: id={document_id}, force={force}")
    
    try:
        rag_service = RAGService(db)
        result = rag_service.embed_document(document_id, force=force)
        
        if result.get("skipped", False):
            logger.info(f"Document {document_id} already embedded (skipped)")
        else:
            logger.info(
                f"Document {document_id} embedded: "
                f"chunks={result['chunks_created']}, "
                f"time={result['processing_time_ms']}ms"
            )
        
        return EmbedDocumentResponse(**result)
        
    except DocumentNotFoundError as e:
        logger.error(f"Document not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
        
    except RAGServiceError as e:
        logger.error(f"RAG service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG service error: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in embed_document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post(
    "/embed_all",
    response_model=EmbedAllResponse,
    status_code=status.HTTP_200_OK,
    responses=COMMON_RAG_RESPONSES,
    summary="Embed all documents",
    description="""
    Chunk and embed all documents in the database for RAG.
    
    This endpoint processes all documents in batch:
    1. Retrieves all documents from the database
    2. For each document, splits it into chunks and generates embeddings
    3. Stores all embeddings in the database
    
    Documents that already have embeddings will be skipped unless you use `force=true`.
    
    **Note:** This operation can take several minutes depending on the number of documents.
    """
)
async def embed_all_documents(
    force: bool = False,
    db: Session = Depends(get_db)
) -> EmbedAllResponse:
    """
    Embed all documents in the database.
    
    Args:
        force: If True, re-embed documents that already have embeddings
        db: Database session (injected)
        
    Returns:
        Aggregate embedding operation results
    """
    logger.info(f"Embedding all documents: force={force}")
    
    try:
        rag_service = RAGService(db)
        result = rag_service.embed_all_documents(force=force)
        
        logger.info(
            f"Batch embedding complete: "
            f"processed={result['documents_processed']}, "
            f"skipped={result['documents_skipped']}, "
            f"chunks={result['total_chunks']}, "
            f"time={result['processing_time_ms']}ms"
        )
        
        # Convert results to DocumentEmbeddingResult schema
        formatted_results = [
            DocumentEmbeddingResult(
                document_id=r["document_id"],
                document_title=r["document_title"],
                chunks_created=r.get("chunks_created", 0),
                embeddings_created=r.get("embeddings_created", 0),
                skipped=r.get("skipped", False),
                error=r.get("error")
            )
            for r in result["results"]
        ]
        
        return EmbedAllResponse(
            documents_processed=result["documents_processed"],
            documents_skipped=result["documents_skipped"],
            total_chunks=result["total_chunks"],
            total_embeddings=result["total_embeddings"],
            processing_time_ms=result["processing_time_ms"],
            results=formatted_results
        )
        
    except RAGServiceError as e:
        logger.error(f"RAG service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG service error: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in embed_all: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=RAGStatsResponse,
    status_code=status.HTTP_200_OK,
    responses=COMMON_RAG_RESPONSES,
    summary="Get RAG system statistics",
    description="""
    Get statistics about the RAG system.
    
    Returns information about:
    - Total number of documents and embeddings
    - Average chunks per document
    - Embedding model and configuration
    - RAG system parameters
    """
)
async def get_rag_stats(
    db: Session = Depends(get_db)
) -> RAGStatsResponse:
    """
    Get RAG system statistics.
    
    Args:
        db: Database session (injected)
        
    Returns:
        RAG system statistics
    """
    logger.info("Fetching RAG statistics")
    
    try:
        rag_service = RAGService(db)
        stats = rag_service.get_stats()
        
        logger.info(
            f"RAG stats retrieved: "
            f"documents={stats['total_documents']}, "
            f"embeddings={stats['total_embeddings']}"
        )
        
        return RAGStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Unexpected error in get_stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

