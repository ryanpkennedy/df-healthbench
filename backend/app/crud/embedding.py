"""
CRUD operations for DocumentEmbedding model.

This module contains all database query operations for document embeddings,
including vector similarity search using PGVector.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Optional, Tuple
import logging

from app.models.document_embedding import DocumentEmbedding
from app.models.document import Document


logger = logging.getLogger(__name__)


def create_embedding(
    db: Session,
    document_id: int,
    chunk_index: int,
    chunk_text: str,
    embedding: List[float]
) -> DocumentEmbedding:
    """
    Create a new document embedding in the database.
    
    Args:
        db: Database session
        document_id: ID of the parent document
        chunk_index: Index of this chunk within the document (0-based)
        chunk_text: The actual text content of this chunk
        embedding: Vector embedding (1536 dimensions)
        
    Returns:
        Created DocumentEmbedding model instance
        
    Example:
        >>> embedding_vec = [0.1, 0.2, ...]  # 1536 dimensions
        >>> emb = create_embedding(db, 1, 0, "Patient has fever", embedding_vec)
        >>> print(f"Created embedding with ID: {emb.id}")
    """
    db_embedding = DocumentEmbedding(
        document_id=document_id,
        chunk_index=chunk_index,
        chunk_text=chunk_text,
        embedding=embedding
    )
    
    db.add(db_embedding)
    db.commit()
    db.refresh(db_embedding)
    
    logger.debug(f"Created embedding: document_id={document_id}, chunk_index={chunk_index}")
    
    return db_embedding


def create_embeddings_batch(
    db: Session,
    embeddings_data: List[dict]
) -> List[DocumentEmbedding]:
    """
    Create multiple embeddings in a single transaction (bulk insert).
    
    This is more efficient than calling create_embedding() multiple times.
    
    Args:
        db: Database session
        embeddings_data: List of dicts with keys: document_id, chunk_index, chunk_text, embedding
        
    Returns:
        List of created DocumentEmbedding instances
        
    Example:
        >>> data = [
        ...     {"document_id": 1, "chunk_index": 0, "chunk_text": "...", "embedding": [...]},
        ...     {"document_id": 1, "chunk_index": 1, "chunk_text": "...", "embedding": [...]}
        ... ]
        >>> embeddings = create_embeddings_batch(db, data)
        >>> print(f"Created {len(embeddings)} embeddings")
    """
    db_embeddings = [
        DocumentEmbedding(
            document_id=data["document_id"],
            chunk_index=data["chunk_index"],
            chunk_text=data["chunk_text"],
            embedding=data["embedding"]
        )
        for data in embeddings_data
    ]
    
    db.add_all(db_embeddings)
    db.commit()
    
    # Refresh all instances to get generated IDs
    for emb in db_embeddings:
        db.refresh(emb)
    
    logger.info(f"Created {len(db_embeddings)} embeddings in batch")
    
    return db_embeddings


def get_embeddings_by_document(
    db: Session,
    document_id: int
) -> List[DocumentEmbedding]:
    """
    Retrieve all embeddings for a specific document.
    
    Args:
        db: Database session
        document_id: ID of the document
        
    Returns:
        List of DocumentEmbedding instances, ordered by chunk_index
        
    Example:
        >>> embeddings = get_embeddings_by_document(db, 1)
        >>> print(f"Document has {len(embeddings)} chunks")
    """
    return (
        db.query(DocumentEmbedding)
        .filter(DocumentEmbedding.document_id == document_id)
        .order_by(DocumentEmbedding.chunk_index)
        .all()
    )


def get_embedding_by_id(
    db: Session,
    embedding_id: int
) -> Optional[DocumentEmbedding]:
    """
    Retrieve a single embedding by ID.
    
    Args:
        db: Database session
        embedding_id: ID of the embedding
        
    Returns:
        DocumentEmbedding instance if found, None otherwise
    """
    return db.query(DocumentEmbedding).filter(DocumentEmbedding.id == embedding_id).first()


def search_similar_chunks(
    db: Session,
    query_embedding: List[float],
    limit: int = 5,
    similarity_threshold: Optional[float] = None
) -> List[Tuple[DocumentEmbedding, float]]:
    """
    Search for similar document chunks using vector similarity (cosine distance).
    
    Uses PGVector's <=> operator for cosine distance. Lower distance = more similar.
    Cosine distance range: 0 (identical) to 2 (opposite).
    
    Args:
        db: Database session
        query_embedding: Query vector (1536 dimensions)
        limit: Maximum number of results to return (default: 5)
        similarity_threshold: Optional minimum similarity score (0-1, where 1 is identical)
                            If provided, only returns chunks above this threshold
        
    Returns:
        List of tuples: (DocumentEmbedding, similarity_score)
        Results are ordered by similarity (most similar first)
        
    Example:
        >>> query_emb = embedding_service.generate_embedding("What medications?")
        >>> results = search_similar_chunks(db, query_emb, limit=3)
        >>> for chunk, score in results:
        ...     print(f"Score: {score:.3f}, Text: {chunk.chunk_text[:50]}...")
    """
    # Convert similarity threshold to distance threshold if provided
    # Cosine similarity: 1 - (cosine_distance / 2)
    # So: cosine_distance = 2 * (1 - similarity)
    distance_threshold = None
    if similarity_threshold is not None:
        distance_threshold = 2 * (1 - similarity_threshold)
    
    # Build query using PGVector's cosine distance operator (<=>)
    # We also join with documents table to get document metadata
    query = (
        db.query(
            DocumentEmbedding,
            DocumentEmbedding.embedding.cosine_distance(query_embedding).label("distance")
        )
        .join(Document, DocumentEmbedding.document_id == Document.id)
    )
    
    # Apply distance threshold if provided
    if distance_threshold is not None:
        query = query.filter(
            DocumentEmbedding.embedding.cosine_distance(query_embedding) <= distance_threshold
        )
    
    # Order by distance (most similar first) and limit results
    results = (
        query
        .order_by(text("distance"))
        .limit(limit)
        .all()
    )
    
    # Convert distance to similarity score (0-1 range, where 1 is most similar)
    # Similarity = 1 - (distance / 2)
    results_with_similarity = [
        (embedding, 1 - (distance / 2))
        for embedding, distance in results
    ]
    
    logger.debug(
        f"Vector search found {len(results_with_similarity)} results "
        f"(limit={limit}, threshold={similarity_threshold})"
    )
    
    return results_with_similarity


def delete_embeddings_by_document(
    db: Session,
    document_id: int
) -> int:
    """
    Delete all embeddings for a specific document.
    
    Args:
        db: Database session
        document_id: ID of the document
        
    Returns:
        Number of embeddings deleted
        
    Example:
        >>> count = delete_embeddings_by_document(db, 1)
        >>> print(f"Deleted {count} embeddings")
    """
    count = (
        db.query(DocumentEmbedding)
        .filter(DocumentEmbedding.document_id == document_id)
        .delete()
    )
    db.commit()
    
    logger.info(f"Deleted {count} embeddings for document_id={document_id}")
    
    return count


def delete_embedding(
    db: Session,
    embedding_id: int
) -> bool:
    """
    Delete a single embedding by ID.
    
    Args:
        db: Database session
        embedding_id: ID of the embedding to delete
        
    Returns:
        True if deleted, False if not found
    """
    embedding = get_embedding_by_id(db, embedding_id)
    if not embedding:
        return False
    
    db.delete(embedding)
    db.commit()
    
    logger.debug(f"Deleted embedding with ID: {embedding_id}")
    
    return True


def count_embeddings(db: Session) -> int:
    """
    Get total count of embeddings in the database.
    
    Args:
        db: Database session
        
    Returns:
        Total number of embeddings
        
    Example:
        >>> total = count_embeddings(db)
        >>> print(f"Total embeddings: {total}")
    """
    return db.query(func.count(DocumentEmbedding.id)).scalar()


def count_embeddings_by_document(db: Session, document_id: int) -> int:
    """
    Get count of embeddings for a specific document.
    
    Args:
        db: Database session
        document_id: ID of the document
        
    Returns:
        Number of embeddings for this document
    """
    return (
        db.query(func.count(DocumentEmbedding.id))
        .filter(DocumentEmbedding.document_id == document_id)
        .scalar()
    )


def get_embedding_stats(db: Session) -> dict:
    """
    Get statistics about embeddings in the database.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with statistics:
        - total_embeddings: Total number of embeddings
        - total_documents_with_embeddings: Number of unique documents that have embeddings
        - avg_chunks_per_document: Average number of chunks per document
        
    Example:
        >>> stats = get_embedding_stats(db)
        >>> print(f"Total embeddings: {stats['total_embeddings']}")
    """
    total_embeddings = count_embeddings(db)
    
    # Count unique documents with embeddings
    total_documents = (
        db.query(func.count(func.distinct(DocumentEmbedding.document_id)))
        .scalar()
    )
    
    # Calculate average chunks per document
    avg_chunks = 0
    if total_documents > 0:
        avg_chunks = total_embeddings / total_documents
    
    return {
        "total_embeddings": total_embeddings,
        "total_documents_with_embeddings": total_documents,
        "avg_chunks_per_document": round(avg_chunks, 2)
    }


def document_has_embeddings(db: Session, document_id: int) -> bool:
    """
    Check if a document has any embeddings.
    
    Args:
        db: Database session
        document_id: ID of the document
        
    Returns:
        True if document has embeddings, False otherwise
    """
    count = count_embeddings_by_document(db, document_id)
    return count > 0

