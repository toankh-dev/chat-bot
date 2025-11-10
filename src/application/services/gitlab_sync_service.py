"""
GitLab Sync Service - Orchestrates synchronization of GitLab repositories to Knowledge Base.
"""

from typing import Dict, List, Any, Optional
import asyncio
from pathlib import Path

from src.infrastructure.external.gitlab_service import GitLabService
from src.application.services.code_chunking_service import CodeChunkingService, CodeChunk
from src.application.services.kb_sync_service import KBSyncService
from src.domain.entities.document import Document
from src.shared.interfaces.repositories.document_repository import DocumentRepository


class GitLabSyncService:
    """Service for synchronizing GitLab repositories to Knowledge Base."""

    def __init__(
        self,
        gitlab_service: GitLabService,
        code_chunking_service: CodeChunkingService,
        kb_sync_service: KBSyncService,
        document_repository: DocumentRepository
    ):
        """
        Initialize GitLab sync service.

        Args:
            gitlab_service: GitLab API service
            code_chunking_service: Code chunking service
            kb_sync_service: Knowledge Base sync service
            document_repository: Document repository
        """
        self.gitlab_service = gitlab_service
        self.code_chunking_service = code_chunking_service
        self.kb_sync_service = kb_sync_service
        self.document_repository = document_repository

    async def sync_repository(
        self,
        repo_url: str,
        branch: str,
        knowledge_base_id: str,
        group_id: str,
        user_id: str,
        domain: str = "general"
    ) -> Dict[str, Any]:
        """
        Sync entire GitLab repository to Knowledge Base.

        Args:
            repo_url: Repository URL
            branch: Branch to sync
            knowledge_base_id: Knowledge Base ID
            group_id: Group ID
            user_id: User ID who triggered sync
            domain: Domain classification

        Returns:
            Dictionary with sync results
        """
        clone_path = None

        try:
            print(f"🔄 Starting repository sync: {repo_url} (branch: {branch})")

            # Step 1: Clone repository
            print("📥 Cloning repository...")
            clone_path = self.gitlab_service.clone_repository(repo_url, branch)

            # Step 2: Get repository info
            project_path = self.gitlab_service._extract_project_path(repo_url)
            project_info = self.gitlab_service.get_project_info(project_path)

            # Step 3: Get file tree
            print("📂 Getting repository tree...")
            tree = self.gitlab_service.get_repository_tree(
                project_id=project_path,
                ref=branch,
                recursive=True
            )

            # Filter only code files
            file_paths = [item["path"] for item in tree if item["type"] == "blob"]
            code_files = self.gitlab_service.filter_code_files(file_paths)

            print(f"✅ Found {len(code_files)} code files")

            # Step 4: Process files in batches
            chunks = []
            processed_files = 0
            failed_files = 0

            for file_path in code_files:
                try:
                    # Read file content from cloned repo
                    full_path = Path(clone_path) / file_path

                    if not full_path.exists():
                        continue

                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Get commit info for metadata
                    commits = self.gitlab_service.gl.projects.get(project_path).commits.list(
                        ref_name=branch,
                        path=file_path,
                        per_page=1
                    )

                    latest_commit = commits[0] if commits else None

                    # Create metadata
                    metadata = {
                        "repo": project_info["name"],
                        "repo_url": repo_url,
                        "branch": branch,
                        "commit": latest_commit.id if latest_commit else "unknown",
                        "commit_message": latest_commit.message if latest_commit else "",
                        "author": latest_commit.author_name if latest_commit else "",
                        "timestamp": latest_commit.created_at if latest_commit else "",
                        "domain": domain,
                        "source_type": "gitlab",
                        "group_id": group_id
                    }

                    # Chunk the file
                    file_chunks = self.code_chunking_service.chunk_by_file(
                        file_path=file_path,
                        content=content,
                        metadata=metadata
                    )

                    chunks.extend(file_chunks)
                    processed_files += 1

                    if processed_files % 10 == 0:
                        print(f"⏳ Processed {processed_files}/{len(code_files)} files...")

                except Exception as e:
                    print(f"⚠️ Failed to process {file_path}: {e}")
                    failed_files += 1
                    continue

            print(f"✅ Processed {processed_files} files, {failed_files} failed")

            # Step 5: Get chunking statistics
            stats = self.code_chunking_service.get_chunking_statistics(chunks)
            print(f"📊 Generated {stats['total_chunks']} chunks from {stats['total_files']} files")

            # Step 6: Sync to Knowledge Base
            print(f"🧠 Syncing to Knowledge Base: {knowledge_base_id}...")

            # Convert CodeChunks to documents
            documents = []
            for chunk in chunks:
                # Create document entity
                doc = Document.create(
                    filename=chunk.metadata["filename"],
                    content_type="text/plain",
                    size_bytes=chunk.metadata["byte_size"],
                    storage_path=chunk.metadata["file_path"],
                    domain=domain,
                    group_id=group_id,
                    uploaded_by=user_id,
                    metadata={
                        **chunk.metadata,
                        "chunk_index": chunk.chunk_index,
                        "source": "gitlab"
                    }
                )
                documents.append(doc)

            # Add to KB (in batches of 50)
            batch_size = 50
            synced_count = 0

            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                batch_texts = [chunks[j].text for j in range(i, min(i + batch_size, len(chunks)))]

                await self.kb_sync_service.add_documents_batch(
                    documents=batch,
                    texts=batch_texts,
                    knowledge_base_id=knowledge_base_id
                )

                synced_count += len(batch)
                print(f"⏳ Synced {synced_count}/{len(documents)} chunks...")

            print(f"✅ Repository sync complete!")

            return {
                "success": True,
                "repository": project_info["name"],
                "branch": branch,
                "files_processed": processed_files,
                "files_failed": failed_files,
                "total_chunks": len(chunks),
                "languages": stats["languages"],
                "total_lines": stats["total_lines"],
                "total_bytes": stats["total_bytes"]
            }

        except Exception as e:
            print(f"❌ Repository sync failed: {e}")
            raise RuntimeError(f"Failed to sync repository: {str(e)}")

        finally:
            # Cleanup cloned repository
            if clone_path:
                self.gitlab_service.cleanup_clone(clone_path)

    async def get_sync_status(
        self,
        group_id: str,
        repo_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get sync status for repositories.

        Args:
            group_id: Group ID
            repo_url: Optional repository URL to filter

        Returns:
            Dictionary with sync status information
        """
        try:
            # Query documents synced from GitLab for this group
            # This is a simple implementation - you might want to add a separate
            # repository_sync table to track sync jobs and their status

            # For now, return basic stats from documents
            filters = {
                "group_id": group_id,
                "metadata.source": "gitlab"
            }

            if repo_url:
                filters["metadata.repo_url"] = repo_url

            # Get document count
            # Note: You'll need to implement a count method in document repository
            # For now, return a placeholder

            return {
                "group_id": group_id,
                "status": "active",
                "repositories": [],  # TODO: Implement repository tracking
                "total_documents": 0,  # TODO: Implement count query
                "last_sync": None  # TODO: Track last sync timestamp
            }

        except Exception as e:
            raise RuntimeError(f"Failed to get sync status: {str(e)}")
