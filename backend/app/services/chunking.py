"""
Document chunking utility for splitting medical documents into semantic chunks.

This module provides functions to intelligently split medical documents (especially
SOAP notes) into smaller chunks suitable for embedding and retrieval.
"""

import logging
import re
from typing import List


logger = logging.getLogger(__name__)


def chunk_document(
    content: str,
    max_chunk_size: int = 800,
    overlap: int = 50,
    preserve_sections: bool = True
) -> List[str]:
    """
    Split a document into semantic chunks for embedding.
    
    This function intelligently splits documents while:
    - Preserving SOAP note structure (Subjective, Objective, Assessment, Plan)
    - Maintaining paragraph boundaries
    - Adding overlap between chunks for context continuity
    - Respecting maximum chunk size limits
    
    Strategy:
    1. First try to split on SOAP section boundaries (S:, O:, A:, P:)
    2. If sections are too large, split on paragraph boundaries (double newlines)
    3. If paragraphs are too large, split on sentence boundaries
    4. Add overlap between chunks to maintain context
    
    Args:
        content: The document text to chunk
        max_chunk_size: Target maximum size for each chunk (default: 800 chars)
        overlap: Number of characters to overlap between chunks (default: 50)
        preserve_sections: Try to keep SOAP sections intact (default: True)
        
    Returns:
        List of text chunks
        
    Raises:
        ValueError: If content is empty or invalid parameters
        
    Example:
        >>> content = "S: Patient reports fever\\n\\nO: Temp 101F\\n\\nA: Viral illness\\n\\nP: Rest and fluids"
        >>> chunks = chunk_document(content)
        >>> len(chunks)
        4  # One chunk per SOAP section
    """
    if not content or not content.strip():
        logger.warning("Attempted to chunk empty content")
        raise ValueError("Content cannot be empty")
    
    if max_chunk_size < 100:
        raise ValueError("max_chunk_size must be at least 100 characters")
    
    if overlap >= max_chunk_size:
        raise ValueError("overlap must be less than max_chunk_size")
    
    content = content.strip()
    logger.debug(f"Chunking document: length={len(content)}, max_chunk_size={max_chunk_size}")
    
    # If content is smaller than max_chunk_size, return as single chunk
    if len(content) <= max_chunk_size:
        logger.debug("Content fits in single chunk")
        return [content]
    
    chunks = []
    
    # Strategy 1: Try to split on SOAP sections if preserve_sections is True
    if preserve_sections:
        soap_chunks = _split_by_soap_sections(content, max_chunk_size)
        if soap_chunks:
            logger.debug(f"Split into {len(soap_chunks)} SOAP sections")
            # Further split any sections that are too large
            for section in soap_chunks:
                if len(section) <= max_chunk_size:
                    chunks.append(section)
                else:
                    # Section is too large, split by paragraphs
                    sub_chunks = _split_by_paragraphs(section, max_chunk_size, overlap)
                    chunks.extend(sub_chunks)
            
            logger.info(f"Document chunked into {len(chunks)} chunks (SOAP-aware)")
            return chunks
    
    # Strategy 2: Split by paragraphs (double newlines)
    chunks = _split_by_paragraphs(content, max_chunk_size, overlap)
    
    logger.info(f"Document chunked into {len(chunks)} chunks (paragraph-based)")
    return chunks


def _split_by_soap_sections(content: str, max_chunk_size: int) -> List[str]:
    """
    Split content by SOAP section markers (S:, O:, A:, P:).
    
    Args:
        content: Document content
        max_chunk_size: Maximum size for each section
        
    Returns:
        List of sections, or empty list if no SOAP structure detected
    """
    # Pattern to match SOAP section headers
    # Matches: "S:", "O:", "A:", "P:" at start of line or after newline
    soap_pattern = r'(?:^|\n)([SOAP]):\s*'
    
    # Find all SOAP section markers
    matches = list(re.finditer(soap_pattern, content, re.MULTILINE))
    
    if len(matches) < 2:
        # Not enough SOAP sections detected
        return []
    
    sections = []
    
    for i, match in enumerate(matches):
        section_label = match.group(1)
        start_pos = match.start()
        
        # Determine end position (start of next section or end of content)
        if i < len(matches) - 1:
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(content)
        
        # Extract section content
        section_content = content[start_pos:end_pos].strip()
        
        if section_content:
            sections.append(section_content)
    
    return sections


def _split_by_paragraphs(content: str, max_chunk_size: int, overlap: int) -> List[str]:
    """
    Split content by paragraph boundaries (double newlines).
    
    Args:
        content: Document content
        max_chunk_size: Maximum size for each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of chunks
    """
    # Split on double newlines (paragraph boundaries)
    paragraphs = re.split(r'\n\s*\n', content)
    
    # Filter out empty paragraphs
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    if not paragraphs:
        return [content]
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed max size
        if current_chunk and len(current_chunk) + len(paragraph) + 2 > max_chunk_size:
            # Save current chunk
            chunks.append(current_chunk.strip())
            
            # Start new chunk with overlap from previous chunk
            if overlap > 0 and len(current_chunk) >= overlap:
                # Take last 'overlap' characters from previous chunk
                overlap_text = current_chunk[-overlap:].strip()
                current_chunk = overlap_text + "\n\n" + paragraph
            else:
                current_chunk = paragraph
        else:
            # Add paragraph to current chunk
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    # Add final chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # Handle case where a single paragraph is larger than max_chunk_size
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_chunk_size:
            final_chunks.append(chunk)
        else:
            # Split large paragraph by sentences
            sentence_chunks = _split_by_sentences(chunk, max_chunk_size, overlap)
            final_chunks.extend(sentence_chunks)
    
    return final_chunks


def _split_by_sentences(content: str, max_chunk_size: int, overlap: int) -> List[str]:
    """
    Split content by sentence boundaries.
    
    Args:
        content: Text content
        max_chunk_size: Maximum size for each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of chunks
    """
    # Split on sentence boundaries (., !, ?)
    sentences = re.split(r'(?<=[.!?])\s+', content)
    
    if not sentences:
        # If no sentence boundaries, split by character count
        return _split_by_character_count(content, max_chunk_size, overlap)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if current_chunk and len(current_chunk) + len(sentence) + 1 > max_chunk_size:
            # Save current chunk
            chunks.append(current_chunk.strip())
            
            # Start new chunk with overlap
            if overlap > 0 and len(current_chunk) >= overlap:
                overlap_text = current_chunk[-overlap:].strip()
                current_chunk = overlap_text + " " + sentence
            else:
                current_chunk = sentence
        else:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
    
    # Add final chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def _split_by_character_count(content: str, max_chunk_size: int, overlap: int) -> List[str]:
    """
    Split content by character count as a last resort.
    
    Args:
        content: Text content
        max_chunk_size: Maximum size for each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of chunks
    """
    chunks = []
    start = 0
    
    while start < len(content):
        end = start + max_chunk_size
        
        # Don't split in the middle of a word
        if end < len(content):
            # Find the last space before max_chunk_size
            last_space = content.rfind(' ', start, end)
            if last_space > start:
                end = last_space
        
        chunk = content[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position, accounting for overlap
        start = end - overlap if overlap > 0 else end
    
    return chunks


def get_chunk_stats(chunks: List[str]) -> dict:
    """
    Get statistics about a list of chunks.
    
    Args:
        chunks: List of text chunks
        
    Returns:
        Dictionary with statistics (count, avg_size, min_size, max_size)
        
    Example:
        >>> chunks = ["chunk 1", "chunk 2", "chunk 3"]
        >>> stats = get_chunk_stats(chunks)
        >>> stats['count']
        3
    """
    if not chunks:
        return {
            "count": 0,
            "avg_size": 0,
            "min_size": 0,
            "max_size": 0,
            "total_chars": 0
        }
    
    sizes = [len(chunk) for chunk in chunks]
    
    return {
        "count": len(chunks),
        "avg_size": sum(sizes) // len(sizes),
        "min_size": min(sizes),
        "max_size": max(sizes),
        "total_chars": sum(sizes)
    }

