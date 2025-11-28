"""
Database seeding module.

This module handles seeding the database with initial data,
particularly SOAP notes from the soap/ directory.
"""

from pathlib import Path
from sqlalchemy.orm import Session
import logging

from app.database import SessionLocal
from app.schemas.document import DocumentCreate
from app.services.document import DocumentService

logger = logging.getLogger(__name__)


def get_soap_notes_directory() -> Path:
    """
    Get the path to the SOAP notes directory.
    
    Returns:
        Path object pointing to the soap/ directory
    """
    # Navigate from backend/app/seed.py to project root/soap/
    backend_dir = Path(__file__).parent.parent
    project_root = backend_dir.parent
    soap_dir = project_root / "soap"
    
    return soap_dir


def load_soap_note(file_path: Path) -> tuple[str, str]:
    """
    Load a SOAP note from a file.
    
    Args:
        file_path: Path to the SOAP note file
        
    Returns:
        Tuple of (title, content)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract title from filename (e.g., "soap_01.txt" -> "SOAP Note 01")
    filename = file_path.stem
    title = f"SOAP Note - {filename.replace('_', ' ').title()}"
    
    return title, content


def seed_soap_notes(db: Session, force: bool = False) -> int:
    """
    Seed the database with SOAP notes.
    
    Args:
        db: Database session
        force: If True, seed even if documents already exist
        
    Returns:
        Number of documents created
        
    Raises:
        FileNotFoundError: If SOAP notes directory not found
    """
    # Check if documents already exist
    existing_docs = DocumentService.get_all_document_ids(db)
    
    if existing_docs.count > 0 and not force:
        logger.info(f"Database already contains {existing_docs.count} documents. Skipping seed.")
        logger.info("Use force=True to seed anyway.")
        return 0
    
    # Get SOAP notes directory
    soap_dir = get_soap_notes_directory()
    
    if not soap_dir.exists():
        logger.error(f"SOAP notes directory not found: {soap_dir}")
        raise FileNotFoundError(f"SOAP notes directory not found: {soap_dir}")
    
    # Find all SOAP note files
    soap_files = sorted(soap_dir.glob("soap_*.txt"))
    
    if not soap_files:
        logger.warning(f"No SOAP note files found in {soap_dir}")
        return 0
    
    logger.info(f"Found {len(soap_files)} SOAP notes to load")
    
    # Load and create documents
    created_count = 0
    
    for soap_file in soap_files:
        try:
            logger.info(f"Loading {soap_file.name}...")
            
            # Load content
            title, content = load_soap_note(soap_file)
            
            # Create document
            doc_data = DocumentCreate(title=title, content=content)
            document = DocumentService.create_new_document(db, doc_data)
            
            logger.info(f"✅ Created document ID {document.id}: {title}")
            created_count += 1
            
        except Exception as e:
            logger.error(f"Failed to load {soap_file.name}: {e}")
            continue
    
    logger.info(f"Successfully seeded {created_count} SOAP notes")
    
    return created_count


def seed_database(force: bool = False) -> None:
    """
    Main function to seed the database with initial data.
    
    Args:
        force: If True, seed even if data already exists
    """
    logger.info("=" * 60)
    logger.info("Database Seeding")
    logger.info("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Seed SOAP notes
        count = seed_soap_notes(db, force=force)
        
        logger.info("=" * 60)
        logger.info(f"Seeding complete: {count} documents created")
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
    
    # Check for --force flag
    force = "--force" in sys.argv
    
    if force:
        logger.info("Force flag detected - will seed even if data exists")
    
    seed_database(force=force)

