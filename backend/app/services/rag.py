"""
RAG (Retrieval-Augmented Generation) service layer.

This module provides high-level orchestration for the RAG pipeline,
coordinating between document chunking, embedding generation, vector search,
and LLM-based answer generation.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.services.embedding import get_embedding_service
from app.services.chunking import chunk_document
from app.services.llm import get_llm_service
from app.crud import document as document_crud
from app.crud import embedding as embedding_crud
from app.models.document import Document


logger = logging.getLogger(__name__)


class RAGServiceError(Exception):
    """Base exception for RAG service errors."""
    pass


class DocumentNotFoundError(RAGServiceError):
    """Raised when a document is not found."""
    pass


class NoEmbeddingsFoundError(RAGServiceError):
    """Raised when no embeddings are found for search."""
    pass


class RAGService:
    """
    Service class for RAG operations.
    
    This class orchestrates the RAG pipeline:
    1. Document chunking
    2. Embedding generation
    3. Vector similarity search
    4. Context-aware answer generation using LLM
    """
    
    def __init__(self, db: Session):
        """
        Initialize RAG service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.embedding_service = get_embedding_service()
        self.llm_service = get_llm_service()
        
        # Load configuration
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.top_k = settings.rag_top_k
    
    def embed_document(
        self,
        document_id: int,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Chunk and embed a single document.
        
        This method:
        1. Retrieves the document from the database
        2. Chunks the document content
        3. Generates embeddings for each chunk
        4. Stores embeddings in the database
        
        Args:
            document_id: ID of the document to embed
            force: If True, re-embed even if embeddings already exist
            
        Returns:
            Dictionary with results:
                - document_id: ID of the document
                - document_title: Title of the document
                - chunks_created: Number of chunks created
                - embeddings_created: Number of embeddings created
                - processing_time_ms: Processing time in milliseconds
                
        Raises:
            DocumentNotFoundError: If document doesn't exist
            
        Example:
            >>> rag_service = RAGService(db)
            >>> result = rag_service.embed_document(1)
            >>> print(f"Created {result['chunks_created']} chunks")
        """
        start_time = time.time()
        
        # Retrieve document
        document = document_crud.get_document(self.db, document_id)
        if not document:
            logger.error(f"Document not found: id={document_id}")
            raise DocumentNotFoundError(f"Document with ID {document_id} not found")
        
        logger.info(f"Embedding document: id={document_id}, title='{document.title}'")
        
        # Check if embeddings already exist
        if not force and embedding_crud.document_has_embeddings(self.db, document_id):
            existing_count = embedding_crud.count_embeddings_by_document(self.db, document_id)
            logger.info(f"Document {document_id} already has {existing_count} embeddings (use force=True to re-embed)")
            
            elapsed_time = (time.time() - start_time) * 1000
            return {
                "document_id": document_id,
                "document_title": document.title,
                "chunks_created": 0,
                "embeddings_created": 0,
                "existing_embeddings": existing_count,
                "processing_time_ms": int(elapsed_time),
                "skipped": True
            }
        
        # Delete existing embeddings if force=True
        if force:
            deleted_count = embedding_crud.delete_embeddings_by_document(self.db, document_id)
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} existing embeddings for document {document_id}")
        
        # Chunk the document
        chunks = chunk_document(
            document.content,
            max_chunk_size=self.chunk_size,
            overlap=self.chunk_overlap,
            preserve_sections=True
        )
        
        logger.info(f"Document chunked into {len(chunks)} chunks")
        
        # Generate embeddings for all chunks (batch processing)
        embeddings = self.embedding_service.generate_embeddings_batch(chunks)
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Prepare data for batch insert
        embeddings_data = [
            {
                "document_id": document_id,
                "chunk_index": i,
                "chunk_text": chunk,
                "embedding": embedding
            }
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
        
        # Store embeddings in database
        created_embeddings = embedding_crud.create_embeddings_batch(self.db, embeddings_data)
        
        elapsed_time = (time.time() - start_time) * 1000
        
        logger.info(
            f"Document embedded successfully: document_id={document_id}, "
            f"chunks={len(chunks)}, elapsed_time_ms={elapsed_time:.2f}"
        )
        
        return {
            "document_id": document_id,
            "document_title": document.title,
            "chunks_created": len(chunks),
            "embeddings_created": len(created_embeddings),
            "processing_time_ms": int(elapsed_time),
            "skipped": False
        }
    
    def embed_all_documents(
        self,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Embed all documents in the database.
        
        Args:
            force: If True, re-embed documents that already have embeddings
            
        Returns:
            Dictionary with results:
                - documents_processed: Number of documents processed
                - documents_skipped: Number of documents skipped (already embedded)
                - total_chunks: Total number of chunks created
                - total_embeddings: Total number of embeddings created
                - processing_time_ms: Total processing time
                - results: List of per-document results
                
        Example:
            >>> rag_service = RAGService(db)
            >>> result = rag_service.embed_all_documents()
            >>> print(f"Processed {result['documents_processed']} documents")
        """
        start_time = time.time()
        
        # Get all documents
        documents = document_crud.get_documents(self.db, skip=0, limit=1000)
        
        logger.info(f"Embedding {len(documents)} documents (force={force})")
        
        results = []
        total_chunks = 0
        total_embeddings = 0
        documents_processed = 0
        documents_skipped = 0
        
        for document in documents:
            try:
                result = self.embed_document(document.id, force=force)
                results.append(result)
                
                total_chunks += result["chunks_created"]
                total_embeddings += result["embeddings_created"]
                
                if result.get("skipped", False):
                    documents_skipped += 1
                else:
                    documents_processed += 1
                    
            except Exception as e:
                logger.error(f"Error embedding document {document.id}: {e}")
                results.append({
                    "document_id": document.id,
                    "document_title": document.title,
                    "error": str(e),
                    "skipped": False
                })
        
        elapsed_time = (time.time() - start_time) * 1000
        
        logger.info(
            f"Batch embedding complete: processed={documents_processed}, "
            f"skipped={documents_skipped}, total_chunks={total_chunks}, "
            f"elapsed_time_ms={elapsed_time:.2f}"
        )
        
        return {
            "documents_processed": documents_processed,
            "documents_skipped": documents_skipped,
            "total_chunks": total_chunks,
            "total_embeddings": total_embeddings,
            "processing_time_ms": int(elapsed_time),
            "results": results
        }
    
    def answer_question(
        self,
        question: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG pipeline.
        
        This method:
        1. Generates an embedding for the question
        2. Searches for similar document chunks using vector similarity
        3. Builds context from retrieved chunks
        4. Calls LLM with context + question to generate answer
        5. Returns answer with source citations
        
        Args:
            question: The question to answer
            top_k: Number of chunks to retrieve (default: from config)
            similarity_threshold: Minimum similarity score (0-1) for retrieved chunks
            model: Optional LLM model override
            
        Returns:
            Dictionary with:
                - answer: The generated answer
                - sources: List of source chunks with metadata
                - model_used: The LLM model used
                - token_usage: Token usage statistics
                - processing_time_ms: Total processing time
                - retrieval_time_ms: Time spent on retrieval
                - generation_time_ms: Time spent on LLM generation
                
        Raises:
            ValueError: If question is empty
            NoEmbeddingsFoundError: If no embeddings exist in database
            
        Example:
            >>> rag_service = RAGService(db)
            >>> result = rag_service.answer_question("What medications are mentioned?")
            >>> print(result['answer'])
            >>> for source in result['sources']:
            ...     print(f"Source: {source['document_title']}")
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")
        
        start_time = time.time()
        top_k = top_k or self.top_k
        
        logger.info(f"Answering question: '{question[:100]}...' (top_k={top_k})")
        
        # Check if any embeddings exist
        total_embeddings = embedding_crud.count_embeddings(self.db)
        if total_embeddings == 0:
            logger.error("No embeddings found in database")
            raise NoEmbeddingsFoundError(
                "No document embeddings found. Please embed documents first using /rag/embed_all"
            )
        
        # Step 1: Generate embedding for the question
        retrieval_start = time.time()
        question_embedding = self.embedding_service.generate_embedding(question)
        
        # Step 2: Search for similar chunks
        similar_chunks = embedding_crud.search_similar_chunks(
            self.db,
            question_embedding,
            limit=top_k,
            similarity_threshold=similarity_threshold
        )
        
        retrieval_time = (time.time() - retrieval_start) * 1000
        
        if not similar_chunks:
            logger.warning("No similar chunks found for question")
            return {
                "answer": "I couldn't find any relevant information in the documents to answer your question.",
                "sources": [],
                "model_used": model or settings.openai_default_model,
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "retrieval_time_ms": int(retrieval_time),
                "generation_time_ms": 0
            }
        
        logger.info(f"Retrieved {len(similar_chunks)} similar chunks")
        
        # Step 3: Build context from retrieved chunks
        context_parts = []
        sources = []
        
        for i, (chunk_embedding, similarity_score) in enumerate(similar_chunks, 1):
            # Get document info
            document = document_crud.get_document(self.db, chunk_embedding.document_id)
            
            context_parts.append(
                f"[Source {i}] Document: {document.title}\n"
                f"{chunk_embedding.chunk_text}\n"
            )
            
            sources.append({
                "document_id": chunk_embedding.document_id,
                "document_title": document.title,
                "chunk_index": chunk_embedding.chunk_index,
                "chunk_text": chunk_embedding.chunk_text,
                "similarity_score": round(similarity_score, 4)
            })
        
        context = "\n".join(context_parts)
        
        # Step 4: Generate answer using LLM
        generation_start = time.time()
        
        system_prompt = """
            You are a medical documentation assistant specialized in summarizing clinical notes.

            Your task is to:
            1. Answer the question based ONLY on the provided context from medical documents
            2. Be accurate and precise - cite specific information from the sources
            3. If the context doesn't contain enough information to answer fully, say so
            4. Use medical terminology appropriately but explain complex terms when helpful
            5. Reference which source(s) you're using (e.g., "According to Source 1...")

            Do not make up information or use knowledge outside the provided context.
        """

        user_prompt = f"""
            Please summarize the following medical note:

            {context}

            Question: {question}

            Please provide a clear, accurate answer based on the context above. Reference the sources you use.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        llm_response = self.llm_service._create_completion(
            messages=messages,
            model=model
        )
        
        generation_time = (time.time() - generation_start) * 1000
        
        answer = llm_response.choices[0].message.content
        
        elapsed_time = (time.time() - start_time) * 1000
        
        logger.info(
            f"Question answered: retrieval_time={retrieval_time:.2f}ms, "
            f"generation_time={generation_time:.2f}ms, total_time={elapsed_time:.2f}ms"
        )
        
        return {
            "answer": answer.strip(),
            "sources": sources,
            "model_used": llm_response.model,
            "token_usage": {
                "prompt_tokens": llm_response.usage.prompt_tokens,
                "completion_tokens": llm_response.usage.completion_tokens,
                "total_tokens": llm_response.usage.total_tokens
            },
            "processing_time_ms": int(elapsed_time),
            "retrieval_time_ms": int(retrieval_time),
            "generation_time_ms": int(generation_time)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the RAG system.
        
        Returns:
            Dictionary with statistics:
                - total_documents: Total number of documents
                - total_embeddings: Total number of embeddings
                - documents_with_embeddings: Number of documents that have embeddings
                - avg_chunks_per_document: Average chunks per document
                - embedding_dimension: Dimension of embeddings
                
        Example:
            >>> rag_service = RAGService(db)
            >>> stats = rag_service.get_stats()
            >>> print(f"Total embeddings: {stats['total_embeddings']}")
        """
        # Get document count
        total_documents = len(document_crud.get_documents(self.db, skip=0, limit=10000))
        
        # Get embedding stats
        embedding_stats = embedding_crud.get_embedding_stats(self.db)
        
        return {
            "total_documents": total_documents,
            "total_embeddings": embedding_stats["total_embeddings"],
            "documents_with_embeddings": embedding_stats["total_documents_with_embeddings"],
            "avg_chunks_per_document": embedding_stats["avg_chunks_per_document"],
            "embedding_dimension": settings.embedding_dimension,
            "embedding_model": settings.openai_embedding_model,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "rag_top_k": settings.rag_top_k
        }

