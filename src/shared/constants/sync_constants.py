"""
Centralized constants for GitLab sync and document processing.

This module contains all hardcoded values extracted from various services
to improve maintainability and configurability.
"""

from typing import Dict, List, Set

# ============================================================================
# BRANCH DEFAULTS
# ============================================================================

DEFAULT_BRANCH: str = "main"
"""Default branch name to use when repository default branch is not specified."""

DEFAULT_BRANCH_FALLBACKS: List[str] = ["main", "master", "develop"]
"""Fallback branch names to try if default branch cannot be determined."""

# ============================================================================
# BATCH PROCESSING CONFIGURATION
# ============================================================================

GITLAB_SYNC_BATCH_SIZE_DEFAULT: int = 50
"""Default number of files to process in each batch during GitLab sync."""

GITLAB_SYNC_BATCH_SIZE_MIN: int = 5
"""Minimum allowed batch size for GitLab sync."""

GITLAB_SYNC_BATCH_SIZE_MAX: int = 200
"""Maximum allowed batch size to prevent memory issues."""

SYNC_QUEUE_BULK_INSERT_BATCH_SIZE: int = 1000
"""Number of queue items to insert in a single bulk operation.
Used to prevent memory issues when syncing large repositories (10,000+ files)."""

SYNC_QUEUE_PROCESSING_TIMEOUT_MINUTES: int = 30
"""Timeout in minutes before a queue item stuck in 'processing' state is considered stale."""

# ============================================================================
# SYNC PRIORITY LEVELS
# ============================================================================

SYNC_PRIORITY_CODE: int = 10
"""Priority for code files (.py, .js, .ts, .java, etc.)"""

SYNC_PRIORITY_DOCS: int = 5
"""Priority for documentation files (.md, .rst, .txt)"""

SYNC_PRIORITY_CONFIG: int = 3
"""Priority for configuration files (.yaml, .yml, .json)"""

SYNC_PRIORITY_OTHER: int = 0
"""Default priority for other file types"""

# ============================================================================
# CODE CHUNKING CONFIGURATION
# ============================================================================

CODE_CHUNK_MAX_FILE_SIZE: int = 50_000
"""Maximum file size in bytes (50KB) before using large file chunking strategy."""

CODE_CHUNK_SIZE: int = 1000
"""Default chunk size in characters for code splitting."""

CODE_CHUNK_OVERLAP: int = 200
"""Default overlap size in characters between consecutive chunks."""

CODE_CHUNK_MAX_LINES_PER_CHUNK: int = 500
"""Maximum number of lines per chunk, regardless of file size."""

CODE_CHUNK_CONFIG_BY_LANGUAGE: Dict[str, Dict[str, int]] = {
    "python": {"chunk_size": 1500, "chunk_overlap": 300},
    "javascript": {"chunk_size": 1000, "chunk_overlap": 200},
    "typescript": {"chunk_size": 1000, "chunk_overlap": 200},
    "java": {"chunk_size": 2000, "chunk_overlap": 400},
    "go": {"chunk_size": 1200, "chunk_overlap": 250},
    "rust": {"chunk_size": 1500, "chunk_overlap": 300},
    "cpp": {"chunk_size": 1800, "chunk_overlap": 350},
    "c": {"chunk_size": 1800, "chunk_overlap": 350},
    "default": {"chunk_size": 1000, "chunk_overlap": 200}
}
"""Language-specific chunking configuration for optimal code splitting."""

# ============================================================================
# FILE FILTERING PATTERNS
# ============================================================================

CODE_EXCLUDE_PATTERNS: List[str] = [
    # Dependencies
    "node_modules/",
    "vendor/",
    "venv/",
    ".venv/",
    "virtualenv/",

    # Build outputs
    "dist/",
    "build/",
    "target/",
    "out/",
    "bin/",

    # Cache directories
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".cache/",

    # Coverage
    "coverage/",
    ".coverage",
    "htmlcov/",

    # Version control
    ".git/",
    ".svn/",
    ".hg/",

    # IDE
    ".vscode/",
    ".idea/",
    ".vs/",

    # Test patterns
    "test_",
    "_test.",
    ".test.",
    "tests/fixtures/",
    "tests/snapshots/",

    # Minified files
    ".min.js",
    ".min.css",
    "-min.js",
    "-min.css",

    # Lock files
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Gemfile.lock",
    "poetry.lock",
    "Pipfile.lock",
    "composer.lock",

    # Binary/compiled
    ".pyc",
    ".pyo",
    ".so",
    ".dll",
    ".exe",
    ".class",
    ".jar",

    # Assets (usually don't need to index)
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
]
"""
Patterns to exclude from code synchronization.
Files/directories matching these patterns will be skipped during sync.
"""

SUPPORTED_CODE_EXTENSIONS: List[str] = [
    # Programming languages
    ".py",      # Python
    ".js",      # JavaScript
    ".ts",      # TypeScript
    ".tsx",     # TypeScript React
    ".jsx",     # JavaScript React
    ".java",    # Java
    ".go",      # Go
    ".rs",      # Rust
    ".cpp",     # C++
    ".cc",      # C++
    ".cxx",     # C++
    ".c",       # C
    ".h",       # C/C++ Header
    ".hpp",     # C++ Header
    ".rb",      # Ruby
    ".php",     # PHP
    ".swift",   # Swift
    ".kt",      # Kotlin
    ".scala",   # Scala
    ".cs",      # C#
    ".fs",      # F#
    ".m",       # Objective-C
    ".r",       # R
    ".jl",      # Julia
    ".lua",     # Lua
    ".pl",      # Perl
    ".sh",      # Shell
    ".bash",    # Bash
    ".zsh",     # Zsh
    ".fish",    # Fish

    # Data & Config
    ".sql",     # SQL
    ".yaml",    # YAML
    ".yml",     # YAML
    ".json",    # JSON
    ".toml",    # TOML
    ".ini",     # INI
    ".conf",    # Config
    ".xml",     # XML

    # Documentation
    ".md",      # Markdown
    ".rst",     # reStructuredText
    ".txt",     # Plain text
    ".adoc",    # AsciiDoc

    # Web
    ".html",    # HTML
    ".htm",     # HTML
    ".css",     # CSS
    ".scss",    # SCSS
    ".sass",    # Sass
    ".less",    # Less
    ".vue",     # Vue
    ".svelte",  # Svelte
]
"""
List of supported code file extensions for synchronization.
Only files with these extensions will be processed during GitLab sync.
"""

# ============================================================================
# GITLAB API CONFIGURATION
# ============================================================================

GITLAB_API_MAX_PER_PAGE: int = 100
"""Maximum items per page allowed by GitLab API."""

GITLAB_API_DEFAULT_PER_PAGE: int = 50
"""Default items per page for GitLab API requests."""

GITLAB_API_TIMEOUT_SECONDS: int = 30
"""Timeout in seconds for GitLab API requests."""

GITLAB_API_MAX_RETRIES: int = 3
"""Maximum number of retries for failed GitLab API requests."""

GITLAB_API_RETRY_DELAY_SECONDS: int = 5
"""Delay in seconds between retry attempts."""

# ============================================================================
# DOCUMENT UPLOAD LIMITS
# ============================================================================

DOCUMENT_MAX_FILE_SIZE_MB: int = 50
"""Maximum file size in megabytes for document uploads."""

DOCUMENT_MAX_FILE_SIZE: int = 50 * 1024 * 1024
"""Maximum file size in bytes for document uploads (computed from MB)."""

DOCUMENT_ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".docx", ".txt", ".md", ".doc", ".rtf"}
"""Allowed file extensions for document uploads."""

DOCUMENT_ALLOWED_CONTENT_TYPES: Set[str] = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "text/markdown",
    "application/rtf",
}
"""Allowed MIME content types for document uploads."""

# ============================================================================
# VECTOR STORE CONFIGURATION
# ============================================================================

VECTOR_STORE_MIN_SUCCESS_RATE: float = 0.9
"""Minimum success rate (0.0-1.0) for vector insertion.
If less than 90% of chunks succeed, the operation fails."""

VECTOR_STORE_BATCH_SIZE: int = 100
"""Number of vectors to insert in a single batch operation."""

# ============================================================================
# CONNECTOR SYNC DEFAULTS
# ============================================================================

CONNECTOR_SYNC_DEFAULTS: Dict[str, int] = {
    "batch_size": 50,
    "concurrent_batches": 2,
    "max_file_size_mb": 5,
    "max_retries": 3,
    "retry_delay_seconds": 60
}
"""Default synchronization configuration for external connectors."""

# ============================================================================
# BRANCH CHANGE BEHAVIOR
# ============================================================================

GITLAB_SYNC_AUTO_CLEANUP_ON_BRANCH_CHANGE: bool = True
"""Automatically cleanup old branch vectors when branch changes."""

GITLAB_SYNC_ABORT_ON_CLEANUP_FAILURE: bool = True
"""Abort sync if cleanup of old branch vectors fails."""
