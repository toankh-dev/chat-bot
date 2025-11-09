"""
Code Chunking Service - Specialized chunking for source code files.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import os
from pathlib import Path


@dataclass
class CodeChunk:
    """Represents a chunk of source code with metadata."""
    text: str
    chunk_index: int
    metadata: Dict[str, Any]


class CodeChunkingService:
    """Service for chunking source code files for embedding."""

    def __init__(self, max_file_size: int = 50000):
        """
        Initialize code chunking service.

        Args:
            max_file_size: Maximum file size in bytes (default 50KB)
        """
        self.max_file_size = max_file_size

        # Language extensions mapping
        self.language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".cs": "csharp",
            ".sql": "sql",
            ".sh": "bash",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".xml": "xml",
            ".md": "markdown",
            ".html": "html",
            ".css": "css",
            ".vue": "vue",
            ".r": "r",
            ".m": "matlab",
            ".dart": "dart"
        }

    def chunk_by_file(
        self,
        file_path: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> List[CodeChunk]:
        """
        Chunk code by file (1 file = 1 chunk for MVP).

        Strategy: Keep entire file as one chunk if under size limit.
        This preserves full context for smaller files.

        Args:
            file_path: Path to the file within repository
            content: File content as string
            metadata: Additional metadata (repo, commit, branch, etc.)

        Returns:
            List of CodeChunk objects

        Raises:
            ValueError: If content is empty or too large
        """
        if not content or not content.strip():
            raise ValueError(f"Cannot chunk empty file: {file_path}")

        # Check file size
        content_size = len(content.encode('utf-8'))

        if content_size > self.max_file_size:
            # File too large, split by logical boundaries
            print(f"⚠️ File {file_path} is {content_size} bytes, splitting...")
            return self._chunk_large_file(file_path, content, metadata)

        # Single chunk for the entire file
        chunk_metadata = self._create_chunk_metadata(
            file_path=file_path,
            content=content,
            base_metadata=metadata,
            chunk_index=0,
            total_chunks=1
        )

        return [CodeChunk(
            text=content,
            chunk_index=0,
            metadata=chunk_metadata
        )]

    def _chunk_large_file(
        self,
        file_path: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> List[CodeChunk]:
        """
        Split large files into multiple chunks.

        Strategy: Split by logical boundaries (classes, functions, sections).
        For Phase 2, we'll implement AST-based splitting.
        For now, use simple line-based splitting.

        Args:
            file_path: Path to the file
            content: File content
            metadata: Base metadata

        Returns:
            List of CodeChunk objects
        """
        lines = content.split('\n')
        total_lines = len(lines)

        # Target ~30KB per chunk
        lines_per_chunk = min(500, total_lines)

        chunks = []
        chunk_index = 0

        for start_line in range(0, total_lines, lines_per_chunk):
            end_line = min(start_line + lines_per_chunk, total_lines)

            chunk_lines = lines[start_line:end_line]
            chunk_content = '\n'.join(chunk_lines)

            if not chunk_content.strip():
                continue

            chunk_metadata = self._create_chunk_metadata(
                file_path=file_path,
                content=chunk_content,
                base_metadata=metadata,
                chunk_index=chunk_index,
                total_chunks=-1,  # Will update after
                line_start=start_line + 1,
                line_end=end_line
            )

            chunks.append(CodeChunk(
                text=chunk_content,
                chunk_index=chunk_index,
                metadata=chunk_metadata
            ))

            chunk_index += 1

        # Update total_chunks in metadata
        for chunk in chunks:
            chunk.metadata["total_chunks"] = len(chunks)

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
        """
        Create comprehensive metadata for a code chunk.

        Args:
            file_path: Path to the file
            content: Chunk content
            base_metadata: Base metadata from repository
            chunk_index: Index of this chunk
            total_chunks: Total number of chunks for this file
            line_start: Starting line number (optional)
            line_end: Ending line number (optional)

        Returns:
            Dictionary with chunk metadata
        """
        # Detect language
        language = self.detect_language(file_path)

        # Get file statistics
        lines = content.split('\n')
        line_count = len(lines)

        # Extract filename and directory
        filename = os.path.basename(file_path)
        directory = os.path.dirname(file_path)

        metadata = {
            **base_metadata,
            "type": "code",
            "file_path": file_path,
            "filename": filename,
            "directory": directory,
            "language": language,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "line_count": line_count,
            "char_count": len(content),
            "byte_size": len(content.encode('utf-8'))
        }

        # Add line numbers if provided
        if line_start is not None:
            metadata["line_start"] = line_start
        if line_end is not None:
            metadata["line_end"] = line_end

        return metadata

    def detect_language(self, file_path: str) -> str:
        """
        Detect programming language from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Language name (e.g., 'python', 'javascript')
        """
        ext = Path(file_path).suffix.lower()
        return self.language_map.get(ext, "unknown")

    def filter_files(
        self,
        file_list: List[str],
        exclude_patterns: Optional[List[str]] = None
    ) -> List[str]:
        """
        Filter source code files.

        Args:
            file_list: List of file paths
            exclude_patterns: Patterns to exclude

        Returns:
            Filtered list of files
        """
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
                "yarn.lock"
            ]

        filtered = []

        for file_path in file_list:
            # Check if it's a code file
            ext = Path(file_path).suffix.lower()
            if ext not in self.language_map:
                continue

            # Check exclude patterns
            should_exclude = any(pattern in file_path for pattern in exclude_patterns)

            if not should_exclude:
                filtered.append(file_path)

        return filtered

    def extract_metadata(
        self,
        file_path: str,
        content: str,
        repo_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract metadata from source code file.

        Args:
            file_path: Path to the file
            content: File content
            repo_info: Repository information

        Returns:
            Dictionary with extracted metadata
        """
        language = self.detect_language(file_path)
        lines = content.split('\n')

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
            "size_bytes": len(content.encode('utf-8'))
        }

    def get_chunking_statistics(self, chunks: List[CodeChunk]) -> Dict[str, Any]:
        """
        Get statistics about code chunks.

        Args:
            chunks: List of code chunks

        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "total_files": 0,
                "languages": {},
                "total_lines": 0,
                "total_bytes": 0
            }

        # Count languages
        languages = {}
        total_lines = 0
        total_bytes = 0

        for chunk in chunks:
            lang = chunk.metadata.get("language", "unknown")
            languages[lang] = languages.get(lang, 0) + 1

            total_lines += chunk.metadata.get("line_count", 0)
            total_bytes += chunk.metadata.get("byte_size", 0)

        # Count unique files (from chunk_index == 0)
        unique_files = len([c for c in chunks if c.chunk_index == 0])

        return {
            "total_chunks": len(chunks),
            "total_files": unique_files,
            "languages": languages,
            "total_lines": total_lines,
            "total_bytes": total_bytes,
            "avg_chunk_size": total_bytes / len(chunks) if chunks else 0
        }

    def create_gitlab_link(
        self,
        repo_url: str,
        file_path: str,
        commit_sha: str,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None
    ) -> str:
        """
        Create GitLab link to specific file and lines.

        Args:
            repo_url: Repository URL
            file_path: Path to file
            commit_sha: Commit SHA
            line_start: Starting line number (optional)
            line_end: Ending line number (optional)

        Returns:
            GitLab URL to the file
        """
        # Base URL format: https://gitlab.com/user/repo/blob/commit/path
        link = f"{repo_url}/blob/{commit_sha}/{file_path}"

        # Add line numbers if provided
        if line_start is not None:
            if line_end is not None and line_end != line_start:
                link += f"#L{line_start}-{line_end}"
            else:
                link += f"#L{line_start}"

        return link
