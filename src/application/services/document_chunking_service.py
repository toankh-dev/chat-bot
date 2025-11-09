"""
Document Chunking Service - Split text into manageable chunks for embedding.
"""

from typing import List, Dict, Any
import re
from dataclasses import dataclass


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    text: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any]


class DocumentChunkingService:
    """Service for splitting documents into chunks for vector embedding."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, max_chunks: int = 500):
        """
        Initialize chunking service.

        Args:
            chunk_size: Target size for each chunk (characters)
            chunk_overlap: Number of characters to overlap between chunks
            max_chunks: Maximum number of chunks per document
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunks = max_chunks

    async def chunk_text(
        self,
        text: str,
        document_id: str,
        filename: str,
        domain: str,
        metadata: Dict[str, Any] = None
    ) -> List[TextChunk]:
        """
        Split text into chunks with overlap.

        Args:
            text: Full text content to chunk
            document_id: ID of the source document
            filename: Original filename
            domain: Domain/category of the document
            metadata: Additional metadata to attach to chunks

        Returns:
            List of TextChunk objects

        Raises:
            ValueError: If text is empty or invalid
        """
        if not text or not text.strip():
            raise ValueError("Cannot chunk empty text")

        # Clean text
        cleaned_text = self._clean_text(text)

        # Split into chunks
        chunks = self._split_with_overlap(cleaned_text)

        # Limit number of chunks
        if len(chunks) > self.max_chunks:
            print(f"Warning: Document has {len(chunks)} chunks, limiting to {self.max_chunks}")
            chunks = chunks[:self.max_chunks]

        # Create TextChunk objects with metadata
        text_chunks = []
        base_metadata = metadata or {}

        for i, (chunk_text, start_char, end_char) in enumerate(chunks):
            chunk_metadata = {
                **base_metadata,
                "document_id": document_id,
                "filename": filename,
                "domain": domain,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "char_start": start_char,
                "char_end": end_char,
                "chunk_size": len(chunk_text)
            }

            text_chunks.append(TextChunk(
                text=chunk_text,
                chunk_index=i,
                start_char=start_char,
                end_char=end_char,
                metadata=chunk_metadata
            ))

        return text_chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)

        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        return text.strip()

    def _split_with_overlap(self, text: str) -> List[tuple]:
        """
        Split text into overlapping chunks.

        Returns:
            List of tuples (chunk_text, start_char, end_char)
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            # Calculate end position
            end = start + self.chunk_size

            # If this is not the last chunk, try to break at sentence boundary
            if end < text_length:
                end = self._find_sentence_boundary(text, start, end)

            # Extract chunk
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append((chunk_text, start, end))

            # Move to next chunk with overlap
            start = end - self.chunk_overlap

            # Prevent infinite loop
            if start <= chunks[-1][1] if chunks else False:
                start = end

        return chunks

    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        """
        Find a good sentence boundary near the end position.

        Args:
            text: Full text
            start: Start position of chunk
            end: Target end position

        Returns:
            Adjusted end position at sentence boundary
        """
        # Look for sentence endings within a window
        search_start = max(start, end - 100)
        search_text = text[search_start:min(end + 50, len(text))]

        # Look for sentence boundaries (., !, ?, newline)
        sentence_endings = ['.', '!', '?', '\n\n']

        best_pos = -1
        for ending in sentence_endings:
            pos = search_text.rfind(ending, 0, end - search_start)
            if pos > best_pos:
                best_pos = pos

        if best_pos > 0:
            # Found a sentence boundary
            return search_start + best_pos + 1

        # No good boundary found, try word boundary
        return self._find_word_boundary(text, end)

    def _find_word_boundary(self, text: str, end: int) -> int:
        """
        Find a word boundary near the end position.

        Args:
            text: Full text
            end: Target end position

        Returns:
            Adjusted end position at word boundary
        """
        if end >= len(text):
            return len(text)

        # Look backwards for a space
        for i in range(end, max(0, end - 50), -1):
            if text[i].isspace():
                return i

        # No space found, return original position
        return end

    async def chunk_by_sections(
        self,
        text: str,
        document_id: str,
        filename: str,
        domain: str,
        section_headers: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> List[TextChunk]:
        """
        Split text by sections (e.g., markdown headers).

        Args:
            text: Full text content
            document_id: ID of the source document
            filename: Original filename
            domain: Domain/category
            section_headers: List of regex patterns for section headers
            metadata: Additional metadata

        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            raise ValueError("Cannot chunk empty text")

        # Default section headers (markdown-style)
        if section_headers is None:
            section_headers = [
                r'^#{1,6}\s+.+$',  # Markdown headers
                r'^\[Page \d+\]$',  # Page markers
            ]

        # Split by sections
        sections = self._split_by_headers(text, section_headers)

        # Create chunks from sections
        text_chunks = []
        base_metadata = metadata or {}
        char_position = 0

        for i, section in enumerate(sections):
            section_text = section.strip()
            if not section_text:
                continue

            # If section is too large, split it further
            if len(section_text) > self.chunk_size:
                sub_chunks = self._split_with_overlap(section_text)
                for j, (chunk_text, rel_start, rel_end) in enumerate(sub_chunks):
                    chunk_metadata = {
                        **base_metadata,
                        "document_id": document_id,
                        "filename": filename,
                        "domain": domain,
                        "section_index": i,
                        "chunk_index": len(text_chunks),
                        "sub_chunk_index": j,
                        "char_start": char_position + rel_start,
                        "char_end": char_position + rel_end,
                        "chunk_size": len(chunk_text)
                    }

                    text_chunks.append(TextChunk(
                        text=chunk_text,
                        chunk_index=len(text_chunks),
                        start_char=char_position + rel_start,
                        end_char=char_position + rel_end,
                        metadata=chunk_metadata
                    ))
            else:
                chunk_metadata = {
                    **base_metadata,
                    "document_id": document_id,
                    "filename": filename,
                    "domain": domain,
                    "section_index": i,
                    "chunk_index": len(text_chunks),
                    "char_start": char_position,
                    "char_end": char_position + len(section_text),
                    "chunk_size": len(section_text)
                }

                text_chunks.append(TextChunk(
                    text=section_text,
                    chunk_index=len(text_chunks),
                    start_char=char_position,
                    end_char=char_position + len(section_text),
                    metadata=chunk_metadata
                ))

            char_position += len(section_text)

        # Limit chunks
        if len(text_chunks) > self.max_chunks:
            text_chunks = text_chunks[:self.max_chunks]

        return text_chunks

    def _split_by_headers(self, text: str, header_patterns: List[str]) -> List[str]:
        """
        Split text by section headers.

        Args:
            text: Full text
            header_patterns: List of regex patterns for headers

        Returns:
            List of section texts
        """
        sections = []
        current_section = []

        lines = text.split('\n')

        for line in lines:
            is_header = False
            for pattern in header_patterns:
                if re.match(pattern, line, re.MULTILINE):
                    is_header = True
                    break

            if is_header:
                # Save previous section
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = []

            current_section.append(line)

        # Add last section
        if current_section:
            sections.append('\n'.join(current_section))

        return sections

    def get_chunking_statistics(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """
        Get statistics about the chunking results.

        Args:
            chunks: List of text chunks

        Returns:
            Dictionary with chunking statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0,
                "total_characters": 0
            }

        chunk_sizes = [len(chunk.text) for chunk in chunks]

        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "total_characters": sum(chunk_sizes),
            "chunk_size_setting": self.chunk_size,
            "chunk_overlap_setting": self.chunk_overlap
        }
