from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import os
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

@dataclass
class CodeChunk:
    text: str
    chunk_index: int
    metadata: Dict[str, Any]

class CodeChunkingService:
    """Service for chunking source code files for embedding, using LangChain splitter."""

    def __init__(self, max_file_size: int = 50000):
        self.max_file_size = max_file_size

        # Mapping từ extension → LangChain Language enum
        self.language_map = {
            ".py": Language.PYTHON,
            ".js": Language.JS,
            ".ts": Language.TS,
            ".tsx": Language.TS,
            ".jsx": Language.JS,
            ".java": Language.JAVA,
            ".go": Language.GO,
            ".rs": Language.RUST,
            ".cpp": Language.CPP,
            ".c": Language.CPP,
            ".h": Language.CPP,
            ".hpp": Language.CPP,
            ".rb": Language.RUBY,
            ".php": Language.PHP,
            ".swift": Language.SWIFT,
            ".kt": Language.KOTLIN,
            ".scala": Language.SCALA,
            ".cs": Language.CSHARP,
            ".sql": "sql",
           ".sh": "bash",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".xml": Language.HTML,
            ".html": Language.HTML,
            ".css": Language.HTML,
            ".vue": Language.HTML,
            ".r": Language.PYTHON,
            ".m": Language.MARKDOWN,
            ".dart": Language.PYTHON,
        }

    def chunk_by_file(
        self,
        file_path: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> List[CodeChunk]:
        if not content or not content.strip():
            # Skip empty files instead of raising error
            return []

        content_size = len(content.encode("utf-8"))
        if content_size > self.max_file_size:
            print(f"⚠️ File {file_path} is {content_size} bytes, splitting...")
            return self._chunk_large_file(file_path, content, metadata)

        # File nhỏ → 1 chunk duy nhất
        chunk_metadata = self._create_chunk_metadata(
            file_path=file_path,
            content=content,
            base_metadata=metadata,
            chunk_index=0,
            total_chunks=1
        )
        return [CodeChunk(text=content, chunk_index=0, metadata=chunk_metadata)]

    def chunk_code(
        self,
        file_path: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> List[CodeChunk]:
        """
        Alias for chunk_by_file for backward compatibility.

        Args:
            file_path: Path to the source file
            content: File content
            metadata: Base metadata for chunks

        Returns:
            List of code chunks
        """
        return self.chunk_by_file(file_path, content, metadata)

    def _chunk_large_file(
        self,
        file_path: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> List[CodeChunk]:
        """
        Split large code file using LangChain RecursiveCharacterTextSplitter.from_language.
        Giữ nguyên ý tưởng 'split theo function/class' nếu có hỗ trợ.
        """
        language = self._detect_langchain_language(file_path)

        splitter = RecursiveCharacterTextSplitter.from_language(
            language=language,
            chunk_size=1000,
            chunk_overlap=200
        )

        chunks_text = splitter.split_text(content)
        chunks: List[CodeChunk] = []

        for i, chunk_text in enumerate(chunks_text):
            chunk_metadata = self._create_chunk_metadata(
                file_path=file_path,
                content=chunk_text,
                base_metadata=metadata,
                chunk_index=i,
                total_chunks=len(chunks_text)
            )
            chunks.append(CodeChunk(
                text=chunk_text,
                chunk_index=i,
                metadata=chunk_metadata
            ))

        return chunks

    def _create_chunk_metadata(
        self,
        file_path: str,
        content: str,
        base_metadata: Dict[str, Any],
        chunk_index: int,
        total_chunks: int,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None
    ) -> Dict[str, Any]:
        language_name = self.detect_language(file_path)
        lines = content.split("\n")
        filename = os.path.basename(file_path)
        directory = os.path.dirname(file_path)

        metadata = {
            **base_metadata,
            "type": "code",
            "file_path": file_path,
            "filename": filename,
            "directory": directory,
            "language": language_name,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "line_count": len(lines),
            "char_count": len(content),
            "byte_size": len(content.encode("utf-8")),
        }

        if line_start is not None:
            metadata["line_start"] = line_start
        if line_end is not None:
            metadata["line_end"] = line_end

        return metadata

    def detect_language(self, file_path: str) -> str:
        ext = Path(file_path).suffix.lower()
        return self.language_map.get(ext, Language.PYTHON).value if hasattr(Language, "value") else str(self.language_map.get(ext, "unknown"))

    def _detect_langchain_language(self, file_path: str):
        ext = Path(file_path).suffix.lower()
        return self.language_map.get(ext, Language.PYTHON)

    def filter_files(self, file_list: List[str], exclude_patterns: Optional[List[str]] = None) -> List[str]:
        if exclude_patterns is None:
            exclude_patterns = [
                "node_modules/",
                "__pycache__/",
                ".git/",
                "dist/",
                "build/",
                "target/",
                ".pytest_cache/",
                "coverage/",
                ".venv/",
                "venv/",
                "test_",
                "_test.",
                ".test.",
                ".min.js",
                ".min.css",
                ".lock",
                "package-lock.json",
                "yarn.lock",
            ]
        filtered = []
        for file_path in file_list:
            ext = Path(file_path).suffix.lower()
            if ext not in self.language_map:
                continue
            if any(p in file_path for p in exclude_patterns):
                continue
            filtered.append(file_path)
        return filtered

    def extract_metadata(self, file_path: str, content: str, repo_info: Dict[str, Any]) -> Dict[str, Any]:
        language = self.detect_language(file_path)
        lines = content.split("\n")
        return {
            "repo": repo_info.get("repo"),
            "repo_url": repo_info.get("repo_url"),
            "branch": repo_info.get("branch"),
            "commit": repo_info.get("commit"),
            "commit_message": repo_info.get("commit_message"),
            "author": repo_info.get("author"),
            "timestamp": repo_info.get("timestamp"),
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "language": language,
            "line_count": len(lines),
            "size_bytes": len(content.encode("utf-8")),
        }

    def get_chunking_statistics(self, chunks: List[CodeChunk]) -> Dict[str, Any]:
        if not chunks:
            return {
                "total_chunks": 0,
                "total_files": 0,
                "languages": {},
                "total_lines": 0,
                "total_bytes": 0,
            }

        languages = {}
        total_lines = 0
        total_bytes = 0

        for chunk in chunks:
            lang = chunk.metadata.get("language", "unknown")
            languages[lang] = languages.get(lang, 0) + 1
            total_lines += chunk.metadata.get("line_count", 0)
            total_bytes += chunk.metadata.get("byte_size", 0)

        unique_files = len([c for c in chunks if c.chunk_index == 0])

        return {
            "total_chunks": len(chunks),
            "total_files": unique_files,
            "languages": languages,
            "total_lines": total_lines,
            "total_bytes": total_bytes,
            "avg_chunk_size": total_bytes / len(chunks) if chunks else 0,
        }

    def create_gitlab_link(
        self,
        repo_url: str,
        file_path: str,
        commit_sha: str,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None
    ) -> str:
        link = f"{repo_url}/blob/{commit_sha}/{file_path}"
        if line_start is not None:
            if line_end is not None and line_end != line_start:
                link += f"#L{line_start}-{line_end}"
            else:
                link += f"#L{line_start}"
        return link
