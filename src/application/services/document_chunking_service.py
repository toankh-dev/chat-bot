from typing import List, Dict, Any
import re
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter  # sử dụng LangChain

@dataclass
class TextChunk:
    text: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any]

class DocumentChunkingService:
    """Service for splitting documents into chunks for embedding, using LangChain splitter."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, max_chunks: int = 500):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunks = max_chunks

        # Khởi tạo LangChain splitter với cùng thông số chunk_size và chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
            length_function=len,
            is_separator_regex=False
        )

    async def chunk_text(
        self,
        text: str,
        document_id: str,
        filename: str,
        domain: str,
        metadata: Dict[str, Any] = None
    ) -> List[TextChunk]:
        if not text or not text.strip():
            raise ValueError("Cannot chunk empty text")

        cleaned_text = self._clean_text(text)

        # Use LangChain to split
        texts = self.splitter.split_text(cleaned_text)
        # Limit number of chunks
        if len(texts) > self.max_chunks:
            print(f"Warning: Document has {len(texts)} chunks, limiting to {self.max_chunks}")
            texts = texts[: self.max_chunks]

        text_chunks: List[TextChunk] = []
        base_metadata = metadata or {}

        for i, chunk_text in enumerate(texts):
            start_char = None
            end_char = None
            # Nếu muốn giữ start_char/end_char, cần tìm vị trí trong cleaned_text
            # (Bản gốc của bạn có tính start/end theo vị trí) => thêm logic sau
            # (đơn giản: tìm chunk_text bắt đầu tại vị trí nào)
            try:
                start_char = cleaned_text.index(chunk_text)
                end_char = start_char + len(chunk_text)
            except ValueError:
                start_char = 0
                end_char = len(chunk_text)

            chunk_metadata = {
                **base_metadata,
                "document_id": document_id,
                "filename": filename,
                "domain": domain,
                "chunk_index": i,
                "total_chunks": len(texts),
                "char_start": start_char,
                "char_end": end_char,
                "chunk_size": len(chunk_text),
            }

            text_chunks.append(TextChunk(
                text=chunk_text,
                chunk_index=i,
                start_char=start_char,
                end_char=end_char,
                metadata=chunk_metadata
            ))

        return text_chunks

    async def chunk_by_sections(
        self,
        text: str,
        document_id: str,
        filename: str,
        domain: str,
        section_headers: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> List[TextChunk]:
        if not text or not text.strip():
            raise ValueError("Cannot chunk empty text")

        if section_headers is None:
            section_headers = [
                r'^#{1,6}\s+.+$',
                r'^\[Page \d+\]$',
            ]

        cleaned_text = self._clean_text(text)
        sections = self._split_by_headers(cleaned_text, section_headers)

        text_chunks: List[TextChunk] = []
        base_metadata = metadata or {}
        char_position = 0

        for i, section in enumerate(sections):
            section_text = section.strip()
            if not section_text:
                continue

            if len(section_text) > self.chunk_size:
                # lớn hơn giới hạn => sử dụng splitter
                texts = self.splitter.split_text(section_text)
                for j, chunk_text in enumerate(texts):
                    try:
                        rel_start = section_text.index(chunk_text)
                    except ValueError:
                        rel_start = 0
                    rel_end = rel_start + len(chunk_text)

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

        if len(text_chunks) > self.max_chunks:
            text_chunks = text_chunks[: self.max_chunks]

        return text_chunks

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        return text.strip()

    def _split_by_headers(self, text: str, header_patterns: List[str]) -> List[str]:
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
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = []
            current_section.append(line)

        if current_section:
            sections.append('\n'.join(current_section))

        return sections

    def get_chunking_statistics(self, chunks: List[TextChunk]) -> Dict[str, Any]:
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
