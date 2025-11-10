"""
Unit tests for CodeChunkingService.
"""

import pytest
from src.application.services.code_chunking_service import CodeChunkingService, CodeChunk


@pytest.fixture
def chunking_service():
    """Create CodeChunkingService instance."""
    return CodeChunkingService(max_file_size=50000)


class TestDetectLanguage:
    """Test detect_language method."""

    def test_detect_python(self, chunking_service):
        """Test detecting Python files."""
        assert chunking_service.detect_language("main.py") == "python"
        assert chunking_service.detect_language("src/app.py") == "python"

    def test_detect_javascript(self, chunking_service):
        """Test detecting JavaScript/TypeScript files."""
        assert chunking_service.detect_language("app.js") == "javascript"
        assert chunking_service.detect_language("App.tsx") == "typescript"
        assert chunking_service.detect_language("Component.jsx") == "javascript"

    def test_detect_various_languages(self, chunking_service):
        """Test detecting various programming languages."""
        test_cases = [
            ("Main.java", "java"),
            ("main.go", "go"),
            ("lib.rs", "rust"),
            ("app.cpp", "cpp"),
            ("script.sh", "bash"),
            ("config.yaml", "yaml"),
            ("data.json", "json"),
        ]

        for file_path, expected_lang in test_cases:
            assert chunking_service.detect_language(file_path) == expected_lang

    def test_detect_unknown_extension(self, chunking_service):
        """Test detecting unknown file extension."""
        assert chunking_service.detect_language("file.xyz") == "unknown"
        assert chunking_service.detect_language("README") == "unknown"


class TestFilterFiles:
    """Test filter_files method."""

    def test_filter_code_files_only(self, chunking_service):
        """Test filtering to include only code files."""
        files = [
            "src/main.py",
            "README.md",
            "config.yaml",
            "image.png",
            "data.csv"
        ]

        result = chunking_service.filter_files(files)

        assert "src/main.py" in result
        assert "README.md" in result
        assert "config.yaml" in result
        assert "image.png" not in result  # Not a code file
        assert "data.csv" not in result  # Not a code file

    def test_filter_excludes_test_files(self, chunking_service):
        """Test filtering excludes test files."""
        files = [
            "src/main.py",
            "test_main.py",
            "src/utils_test.py",
            "tests/test_app.py"
        ]

        result = chunking_service.filter_files(files)

        assert "src/main.py" in result
        assert "test_main.py" not in result
        assert "src/utils_test.py" not in result
        assert "tests/test_app.py" not in result

    def test_filter_excludes_build_directories(self, chunking_service):
        """Test filtering excludes build directories."""
        files = [
            "src/app.js",
            "node_modules/package/index.js",
            "dist/bundle.js",
            "build/output.js",
            "__pycache__/module.pyc"
        ]

        result = chunking_service.filter_files(files)

        assert "src/app.js" in result
        assert "node_modules/package/index.js" not in result
        assert "dist/bundle.js" not in result
        assert "build/output.js" not in result
        assert "__pycache__/module.pyc" not in result

    def test_filter_with_custom_exclude_patterns(self, chunking_service):
        """Test filtering with custom exclude patterns."""
        files = [
            "src/main.py",
            "legacy/old_code.py",
            "deprecated/module.py"
        ]

        result = chunking_service.filter_files(
            files,
            exclude_patterns=["legacy/", "deprecated/"]
        )

        assert "src/main.py" in result
        assert "legacy/old_code.py" not in result
        assert "deprecated/module.py" not in result


class TestChunkByFile:
    """Test chunk_by_file method."""

    def test_chunk_small_file(self, chunking_service):
        """Test chunking a small file (under size limit)."""
        file_path = "src/main.py"
        content = "def main():\n    print('Hello, World!')\n"
        metadata = {
            "repo": "test-repo",
            "branch": "main",
            "commit": "abc123"
        }

        chunks = chunking_service.chunk_by_file(file_path, content, metadata)

        assert len(chunks) == 1
        assert chunks[0].text == content
        assert chunks[0].chunk_index == 0
        assert chunks[0].metadata["filename"] == "main.py"
        assert chunks[0].metadata["language"] == "python"
        assert chunks[0].metadata["total_chunks"] == 1

    def test_chunk_large_file(self, chunking_service):
        """Test chunking a large file (over size limit)."""
        # Create content larger than max_file_size
        file_path = "src/large.py"
        content = "# Line\n" * 10000  # ~70KB
        metadata = {"repo": "test-repo"}

        chunks = chunking_service.chunk_by_file(file_path, content, metadata)

        # Should split into multiple chunks
        assert len(chunks) > 1
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert chunk.metadata["total_chunks"] == len(chunks)
            assert len(chunk.text) > 0

    def test_chunk_empty_content_raises_error(self, chunking_service):
        """Test chunking empty content raises ValueError."""
        with pytest.raises(ValueError, match="Cannot chunk empty file"):
            chunking_service.chunk_by_file("empty.py", "", {})

    def test_chunk_whitespace_only_raises_error(self, chunking_service):
        """Test chunking whitespace-only content raises ValueError."""
        with pytest.raises(ValueError, match="Cannot chunk empty file"):
            chunking_service.chunk_by_file("whitespace.py", "   \n\n  ", {})

    def test_chunk_metadata_includes_repo_info(self, chunking_service):
        """Test chunk metadata includes repository information."""
        file_path = "src/app.js"
        content = "console.log('test');"
        metadata = {
            "repo": "my-repo",
            "repo_url": "https://gitlab.com/user/repo",
            "branch": "develop",
            "commit": "def456",
            "author": "Test User"
        }

        chunks = chunking_service.chunk_by_file(file_path, content, metadata)

        chunk_meta = chunks[0].metadata
        assert chunk_meta["repo"] == "my-repo"
        assert chunk_meta["repo_url"] == "https://gitlab.com/user/repo"
        assert chunk_meta["branch"] == "develop"
        assert chunk_meta["commit"] == "def456"
        assert chunk_meta["author"] == "Test User"


class TestExtractMetadata:
    """Test extract_metadata method."""

    def test_extract_metadata_python_file(self, chunking_service):
        """Test extracting metadata from Python file."""
        file_path = "src/main.py"
        content = "#!/usr/bin/env python\n" * 100
        repo_info = {
            "repo": "test-repo",
            "repo_url": "https://gitlab.com/user/test-repo",
            "branch": "main",
            "commit": "abc123"
        }

        metadata = chunking_service.extract_metadata(file_path, content, repo_info)

        assert metadata["filename"] == "main.py"
        assert metadata["language"] == "python"
        assert metadata["line_count"] == 100
        assert metadata["size_bytes"] > 0

    def test_extract_metadata_includes_all_repo_info(self, chunking_service):
        """Test metadata includes all repository information."""
        file_path = "app.js"
        content = "// JavaScript"
        repo_info = {
            "repo": "my-repo",
            "repo_url": "https://gitlab.com/user/my-repo",
            "branch": "feature/test",
            "commit": "def456",
            "commit_message": "Add feature",
            "author": "Developer",
            "timestamp": "2024-01-15T10:00:00Z"
        }

        metadata = chunking_service.extract_metadata(file_path, content, repo_info)

        assert metadata["repo"] == "my-repo"
        assert metadata["commit_message"] == "Add feature"
        assert metadata["author"] == "Developer"
        assert metadata["timestamp"] == "2024-01-15T10:00:00Z"


class TestGetChunkingStatistics:
    """Test get_chunking_statistics method."""

    def test_statistics_for_multiple_chunks(self, chunking_service):
        """Test getting statistics for multiple chunks."""
        chunks = [
            CodeChunk(
                text="print('hello')",
                chunk_index=0,
                metadata={"language": "python", "line_count": 1, "byte_size": 15, "file_path": "a.py"}
            ),
            CodeChunk(
                text="console.log('hi')",
                chunk_index=0,
                metadata={"language": "javascript", "line_count": 1, "byte_size": 18, "file_path": "b.js"}
            ),
            CodeChunk(
                text="print('world')",
                chunk_index=1,
                metadata={"language": "python", "line_count": 1, "byte_size": 15, "file_path": "a.py"}
            )
        ]

        stats = chunking_service.get_chunking_statistics(chunks)

        assert stats["total_chunks"] == 3
        assert stats["total_files"] == 2  # Only chunks with index=0
        assert stats["languages"]["python"] == 2
        assert stats["languages"]["javascript"] == 1
        assert stats["total_lines"] == 3
        assert stats["total_bytes"] == 48
        assert stats["avg_chunk_size"] == 16

    def test_statistics_for_empty_list(self, chunking_service):
        """Test getting statistics for empty chunk list."""
        stats = chunking_service.get_chunking_statistics([])

        assert stats["total_chunks"] == 0
        assert stats["total_files"] == 0
        assert stats["languages"] == {}
        assert stats["total_lines"] == 0
        assert stats["total_bytes"] == 0


class TestCreateGitLabLink:
    """Test create_gitlab_link method."""

    def test_create_link_without_lines(self, chunking_service):
        """Test creating GitLab link without line numbers."""
        link = chunking_service.create_gitlab_link(
            repo_url="https://gitlab.com/user/repo",
            file_path="src/main.py",
            commit_sha="abc123"
        )

        assert link == "https://gitlab.com/user/repo/blob/abc123/src/main.py"

    def test_create_link_with_single_line(self, chunking_service):
        """Test creating GitLab link with single line number."""
        link = chunking_service.create_gitlab_link(
            repo_url="https://gitlab.com/user/repo",
            file_path="src/main.py",
            commit_sha="abc123",
            line_start=42
        )

        assert link == "https://gitlab.com/user/repo/blob/abc123/src/main.py#L42"

    def test_create_link_with_line_range(self, chunking_service):
        """Test creating GitLab link with line range."""
        link = chunking_service.create_gitlab_link(
            repo_url="https://gitlab.com/user/repo",
            file_path="src/main.py",
            commit_sha="abc123",
            line_start=10,
            line_end=20
        )

        assert link == "https://gitlab.com/user/repo/blob/abc123/src/main.py#L10-20"

    def test_create_link_same_start_end_line(self, chunking_service):
        """Test creating link when start and end line are the same."""
        link = chunking_service.create_gitlab_link(
            repo_url="https://gitlab.com/user/repo",
            file_path="src/main.py",
            commit_sha="abc123",
            line_start=15,
            line_end=15
        )

        # Should only show single line, not range
        assert link == "https://gitlab.com/user/repo/blob/abc123/src/main.py#L15"
