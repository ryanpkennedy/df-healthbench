"""
Database seeding module.

This module handles seeding the database with initial data,
particularly medical documents from the med_docs/ directory (both text and PDF files),
and optionally generating embeddings for RAG.
"""

from pathlib import Path
from sqlalchemy.orm import Session
import logging
from typing import List

from app.database import SessionLocal
from app.schemas.document import DocumentCreate
from app.services.document import DocumentService

logger = logging.getLogger(__name__)


def get_medical_docs_directory() -> Path:
    """
    Get the path to the medical documents directory.
    
    Returns:
        Path object pointing to the med_docs/ directory
    """
    # In Docker: /app/med_docs
    # Locally: navigate from backend/app/seed.py to project root/med_docs/
    
    # Try Docker path first
    docker_path = Path("/app/med_docs")
    if docker_path.exists():
        return docker_path
    
    # Fall back to local development path
    backend_dir = Path(__file__).parent.parent
    project_root = backend_dir.parent
    med_docs_dir = project_root / "med_docs"
    
    return med_docs_dir


def extract_text_from_pdf(file_path: Path) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text content (sanitized to remove NUL bytes)
        
    Raises:
        ImportError: If pypdf is not installed
        Exception: If PDF extraction fails
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.error("pypdf library not installed. Run: poetry add pypdf")
        raise ImportError("pypdf library required for PDF support")
    
    try:
        reader = PdfReader(file_path)
        text_parts = []
        
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            if text.strip():
                text_parts.append(text)
        
        content = "\n\n".join(text_parts)
        
        # Sanitize: Remove NUL bytes (0x00) which PostgreSQL TEXT columns cannot handle
        # This is common in PDFs with embedded binary data or special formatting
        content = content.replace('\x00', '')
        
        # Also remove other potentially problematic control characters
        # Keep only newlines, tabs, and printable characters
        content = ''.join(char for char in content if char == '\n' or char == '\t' or ord(char) >= 32 or ord(char) == 13)
        
        logger.debug(f"Extracted {len(content)} characters from {file_path.name} ({len(reader.pages)} pages)")
        
        return content
        
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {file_path.name}: {e}")
        raise


def load_document(file_path: Path) -> tuple[str, str]:
    """
    Load a document from a file (supports .txt and .pdf).
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Tuple of (title, content)
        
    Raises:
        ValueError: If file type is not supported
    """
    file_ext = file_path.suffix.lower()
    
    # Generate title from filename
    filename = file_path.stem
    
    # Determine document type from parent directory
    parent_dir = file_path.parent.name
    if parent_dir == "soap":
        title_prefix = "SOAP Note"
    elif parent_dir == "policy":
        title_prefix = "Policy Document"
    else:
        title_prefix = "Medical Document"
    
    # Clean up filename for title
    clean_name = filename.replace('_', ' ').replace('-', ' ').title()
    title = f"{title_prefix} - {clean_name}"
    
    # Load content based on file type
    if file_ext == ".txt":
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    elif file_ext == ".pdf":
        content = extract_text_from_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}. Only .txt and .pdf are supported.")
    
    return title, content


def find_all_documents(base_dir: Path) -> List[Path]:
    """
    Find all supported document files in the medical docs directory.
    
    Searches recursively for .txt and .pdf files in subdirectories.
    
    Args:
        base_dir: Base directory to search (med_docs/)
        
    Returns:
        List of Path objects for all found documents
    """
    documents = []
    
    # Search for text files
    documents.extend(base_dir.glob("**/*.txt"))
    
    # Search for PDF files
    documents.extend(base_dir.glob("**/*.pdf"))
    
    # Filter out any hidden files or system files
    documents = [
        doc for doc in documents 
        if not doc.name.startswith('.') and doc.name.lower() != 'overview.md'
    ]
    
    # Sort by path for consistent ordering
    documents.sort()
    
    return documents


def seed_documents(db: Session, force: bool = False) -> int:
    """
    Seed the database with medical documents (SOAP notes and policy documents).
    
    Supports both .txt and .pdf files from the med_docs/ directory.
    Intelligently detects new documents by comparing available files with database count.
    
    Args:
        db: Database session
        force: If True, re-seed all documents even if they exist
        
    Returns:
        Number of documents created
        
    Raises:
        FileNotFoundError: If medical docs directory not found
    """
    # Get medical docs directory
    med_docs_dir = get_medical_docs_directory()
    
    if not med_docs_dir.exists():
        logger.error(f"Medical docs directory not found: {med_docs_dir}")
        raise FileNotFoundError(f"Medical docs directory not found: {med_docs_dir}")
    
    # Find all document files (txt and pdf)
    doc_files = find_all_documents(med_docs_dir)
    
    if not doc_files:
        logger.warning(f"No document files found in {med_docs_dir}")
        return 0
    
    # Check existing documents
    existing_docs = DocumentService.get_all_document_ids(db)
    available_files_count = len(doc_files)
    existing_db_count = existing_docs.count
    
    logger.info(f"Found {available_files_count} document files in med_docs/")
    logger.info(f"Database currently contains {existing_db_count} documents")
    
    # Intelligent seeding logic
    if force:
        logger.info("Force flag set - will re-seed all documents")
    elif existing_db_count >= available_files_count:
        logger.info(
            f"Database has {existing_db_count} documents, "
            f"same or more than available files ({available_files_count}). Skipping seed."
        )
        logger.info("Use --force flag to re-seed anyway.")
        return 0
    elif existing_db_count > 0:
        logger.info(
            f"⚠️  Database has {existing_db_count} documents but {available_files_count} files available. "
            f"New documents detected! Seeding {available_files_count - existing_db_count} new documents..."
        )
    
    logger.info(f"Processing {len(doc_files)} document files:")
    
    # Group by type for logging
    txt_files = [f for f in doc_files if f.suffix == '.txt']
    pdf_files = [f for f in doc_files if f.suffix == '.pdf']
    logger.info(f"  - {len(txt_files)} text files")
    logger.info(f"  - {len(pdf_files)} PDF files")
    
    # Get existing document titles to avoid duplicates (unless force=True)
    existing_titles = set()
    if not force and existing_db_count > 0:
        logger.info("Fetching existing document titles to avoid duplicates...")
        existing_documents = DocumentService.get_all_documents(db, skip=0, limit=1000)
        existing_titles = {doc.title for doc in existing_documents}
        logger.info(f"Found {len(existing_titles)} existing documents in database")
    
    # Load and create documents
    created_count = 0
    skipped_count = 0
    failed_count = 0
    
    for doc_file in doc_files:
        try:
            # Load content (handles both txt and pdf)
            title, content = load_document(doc_file)
            
            # Check if document already exists (skip duplicates unless force=True)
            if not force and title in existing_titles:
                logger.debug(f"⏭️  Skipping {doc_file.name}: already exists in database")
                skipped_count += 1
                continue
            
            logger.info(f"Loading {doc_file.relative_to(med_docs_dir)}...")
            
            # Validate content
            if not content or len(content.strip()) < 10:
                logger.warning(f"Skipping {doc_file.name}: content too short or empty")
                failed_count += 1
                continue
            
            # Create document
            doc_data = DocumentCreate(title=title, content=content)
            document = DocumentService.create_new_document(db, doc_data)
            
            logger.info(f"✅ Created document ID {document.id}: {title} ({len(content)} chars)")
            created_count += 1
            
        except Exception as e:
            logger.error(f"Failed to load {doc_file.name}: {e}")
            failed_count += 1
            continue
    
    logger.info(
        f"Seeding complete: {created_count} created, "
        f"{skipped_count} skipped (already exist), "
        f"{failed_count} failed"
    )
    
    return created_count


def seed_embeddings(db: Session, skip_embeddings: bool = False) -> dict:
    """
    Generate embeddings for all documents that don't have them.
    
    Args:
        db: Database session
        skip_embeddings: If True, skip embedding generation
        
    Returns:
        Dictionary with embedding statistics
    """
    if skip_embeddings:
        logger.info("Skipping embedding generation (--skip-embeddings flag)")
        return {"skipped": True, "documents_embedded": 0, "total_chunks": 0}
    
    try:
        from app.services.rag import RAGService
        from app.crud import embedding as embedding_crud
        
        # Check if any documents need embedding
        total_docs = len(DocumentService.get_all_documents(db, skip=0, limit=1000))
        total_embeddings = embedding_crud.count_embeddings(db)
        
        if total_embeddings > 0:
            logger.info(f"Embeddings already exist ({total_embeddings} embeddings). Skipping.")
            return {"skipped": True, "documents_embedded": 0, "total_chunks": total_embeddings}
        
        if total_docs == 0:
            logger.info("No documents to embed")
            return {"skipped": True, "documents_embedded": 0, "total_chunks": 0}
        
        logger.info(f"Generating embeddings for {total_docs} documents...")
        
        # Create RAG service and embed all documents
        rag_service = RAGService(db)
        result = rag_service.embed_all_documents(force=False)
        
        logger.info(
            f"✅ Embedding complete: {result['documents_processed']} documents, "
            f"{result['total_chunks']} chunks, "
            f"{result['processing_time_ms']}ms"
        )
        
        return {
            "skipped": False,
            "documents_embedded": result['documents_processed'],
            "total_chunks": result['total_chunks'],
            "processing_time_ms": result['processing_time_ms']
        }
        
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        logger.warning("Continuing without embeddings - you can generate them later via /rag/embed_all")
        return {"skipped": True, "documents_embedded": 0, "total_chunks": 0, "error": str(e)}


def seed_database(force: bool = False, skip_embeddings: bool = False) -> None:
    """
    Main function to seed the database with initial data.
    
    Args:
        force: If True, seed even if data already exists
        skip_embeddings: If True, skip embedding generation
    """
    logger.info("=" * 60)
    logger.info("Database Seeding")
    logger.info("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Seed medical documents (SOAP notes and policy documents)
        count = seed_documents(db, force=force)
        
        logger.info("=" * 60)
        logger.info(f"Document seeding complete: {count} documents created")
        logger.info("=" * 60)
        
        # Generate embeddings if documents were created or if embeddings don't exist
        if count > 0 or not skip_embeddings:
            logger.info("")
            logger.info("=" * 60)
            logger.info("Embedding Generation")
            logger.info("=" * 60)
            
            embedding_result = seed_embeddings(db, skip_embeddings=skip_embeddings)
            
            if not embedding_result.get("skipped", False):
                logger.info("=" * 60)
                logger.info(
                    f"Embedding complete: {embedding_result['documents_embedded']} documents, "
                    f"{embedding_result['total_chunks']} chunks"
                )
                logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Run seeding when script is executed directly
    import sys
    
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Check for flags
    force = "--force" in sys.argv
    skip_embeddings = "--skip-embeddings" in sys.argv
    
    if force:
        logger.info("Force flag detected - will seed even if data exists")
    
    if skip_embeddings:
        logger.info("Skip embeddings flag detected - will not generate embeddings")
    
    seed_database(force=force, skip_embeddings=skip_embeddings)

