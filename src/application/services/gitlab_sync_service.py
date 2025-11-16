"""
GitLab Sync Service - Enhanced with incremental sync and queue-based processing.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from infrastructure.external.gitlab_service import GitLabService
from application.services.code_chunking_service import CodeChunkingService
from application.services.kb_sync_service import KBSyncService
from application.services.connector_service import ConnectorService
from infrastructure.postgresql.repositories.repository_repository import RepositoryRepository
from infrastructure.postgresql.repositories.user_connection_repository import UserConnectionRepository
from infrastructure.postgresql.repositories.sync_history_repository import SyncHistoryRepository
from infrastructure.postgresql.repositories.sync_queue_repository import SyncQueueRepository
from infrastructure.postgresql.repositories.file_change_history_repository import FileChangeHistoryRepository
from infrastructure.postgresql.repositories.commit_model_repository import CommitRepository
from infrastructure.postgresql.repositories.connector_repository import ConnectorRepository
from infrastructure.postgresql.models.knowledge_base_source_model import KnowledgeBaseSourceModel
from infrastructure.postgresql.repositories.knowledge_base_repository import KnowledgeBaseRepository
from infrastructure.postgresql.repositories.knowledge_base_source_repository import KnowledgeBaseSourceRepository
from infrastructure.postgresql.models.repository_model import RepositoryModel
from infrastructure.postgresql.models.sync_history_model import SyncHistoryModel
from infrastructure.postgresql.models.sync_queue_model import SyncQueueModel
from infrastructure.postgresql.models.file_change_history_model import FileChangeHistoryModel
from core.logger import logger
from core.errors import (
    ConnectorNotFoundError,
    KnowledgeBaseNotFoundError,
    VectorCleanupException
)
from shared.constants import DEFAULT_BRANCH, GITLAB_SYNC_BATCH_SIZE_DEFAULT, SYNC_QUEUE_BULK_INSERT_BATCH_SIZE


class GitLabSyncService:
    """Enhanced GitLab sync service with incremental sync support."""

    def __init__(
        self,
        # 9 Repository dependencies (all SYNC)
        repository_repository: RepositoryRepository,
        commit_repository: CommitRepository,
        sync_queue_repository: SyncQueueRepository,
        file_change_history_repository: FileChangeHistoryRepository,
        sync_history_repository: SyncHistoryRepository,
        connector_repository: ConnectorRepository,
        user_connection_repository: UserConnectionRepository,
        knowledge_base_repository: KnowledgeBaseRepository,
        kb_source_repository: KnowledgeBaseSourceRepository,
        # 5 Service dependencies (added redis_lock_service for concurrent sync prevention)
        kb_sync_service: KBSyncService,
        code_chunking_service: CodeChunkingService,
        connector_service: ConnectorService,
        kb_cleanup_service,
        redis_lock_service,
    ):
        """
        Initialize GitLab sync service with all dependencies injected.

        Args:
            repository_repository: Repository repository instance
            commit_repository: Commit repository instance
            sync_queue_repository: Sync queue repository instance
            file_change_history_repository: File change history repository instance
            sync_history_repository: Sync history repository instance
            connector_repository: Connector repository instance
            user_connection_repository: User connection repository instance
            knowledge_base_repository: Knowledge base repository instance (SYNC)
            kb_source_repository: KB source repository instance (SYNC)
            kb_sync_service: Knowledge Base sync service
            code_chunking_service: Code chunking service
            connector_service: Connector service
            kb_cleanup_service: KB Cleanup service (Phase 3.4) - for vector cleanup operations
        """
        # Repository dependencies
        self.repository_repo = repository_repository
        self.commit_repository = commit_repository
        self.sync_queue_repo = sync_queue_repository
        self.file_change_repo = file_change_history_repository
        self.sync_history_repo = sync_history_repository
        self.connector_repo = connector_repository
        self.connection_repo = user_connection_repository
        self.knowledge_base_repo = knowledge_base_repository
        self.kb_source_repo = kb_source_repository

        # Service dependencies
        self.kb_sync_service = kb_sync_service
        self.code_chunking_service = code_chunking_service
        self.connector_service = connector_service
        self.kb_cleanup_service = kb_cleanup_service
        self.redis_lock_service = redis_lock_service

    async def sync_repository_full(
        self,
        user_id: int,
        connector_id: int,
        repository_external_id: str,
        knowledge_base_id: int,
        branch: str,
        auto_sync: bool = False,
    ) -> Dict[str, Any]:
        """
        Perform full repository sync with distributed lock to prevent concurrent syncs.

        Args:
            repository_external_id: External repository ID (GitLab project ID)
            knowledge_base_id: Knowledge Base ID
            user_id: User ID
            branch: Branch to sync
            auto_sync: Enable automatic sync on future changes

        Returns:
            Dictionary with sync results

        Raises:
            SyncInProgressError: If sync already in progress for this repo/branch (409)
            ConnectorNotFoundError: If GitLab connector not found (404)
            KnowledgeBaseNotFoundError: If knowledge base not found (404)
            GitLabAPIError: If GitLab API request fails (502)
        """
        # Generate lock key: sync_lock:repo:{repo_id}:branch:{branch}
        lock_key = f"sync_lock:repo:{repository_external_id}:branch:{branch or 'default'}"

        # Acquire distributed lock (raises SyncInProgressError if already locked)
        with self.redis_lock_service.acquire_lock(lock_key, blocking=False):
            logger.info(
                f"Sync lock acquired, starting repository sync",
                extra={
                    "lock_key": lock_key,
                    "repo_id": repository_external_id,
                    "branch": branch,
                    "user_id": user_id,
                    "kb_id": knowledge_base_id,
                },
            )

            # Perform sync operation within lock context
            return await self._sync_repository_full_impl(
                user_id=user_id,
                connector_id=connector_id,
                repository_external_id=repository_external_id,
                knowledge_base_id=knowledge_base_id,
                branch=branch,
                auto_sync=auto_sync,
            )

    async def _sync_repository_full_impl(
        self,
        user_id: int,
        connector_id: int,
        repository_external_id: str,
        knowledge_base_id: int,
        branch: str,
        auto_sync: bool = False,
    ) -> Dict[str, Any]:
        """
        Internal implementation of full repository sync (called within lock context).

        Args:
            Same as sync_repository_full

        Returns:
            Dictionary with sync results
        """
        # Step 1: Get GitLab service
        gitlab_connector = self.connector_service.get_connector_by_id(connector_id)
        if not gitlab_connector:
            raise ConnectorNotFoundError(
                connector_type="gitlab",
                message="GitLab connector not configured"
            )

        gitlab_service = self.connector_service.get_gitlab_service(gitlab_connector)

        # Step 2. Get or create system connection properly
        connection = self.connector_service.get_or_create_system_connection(
            user_id=user_id, connector=gitlab_connector
        )

        # Step 3: Fetch repository information
        project_info = gitlab_service.get_project_info(repository_external_id)
        repository_external_id = str(project_info["id"])
        branch = branch if branch else project_info.get("default_branch", DEFAULT_BRANCH)

        # Step 3.1: Fetch HEAD commit SHA of the branch
        head_commit_info = gitlab_service.get_branch_head_commit(repository_external_id, branch)
        head_commit_sha = head_commit_info["commit_sha"]

        # STEP 4: GET OR CREATE KNOWLEDGE BASE
        kb_entity = self.knowledge_base_repo.get_by_id(knowledge_base_id)

        if not kb_entity:
            raise KnowledgeBaseNotFoundError(kb_id=knowledge_base_id)
    
        # Step 5. Get or create repository record
        repo, = self.repository_repo.get_or_create(
            connection_id=connection.id,
            external_id=repository_external_id,
            defaults={
                "name": project_info.get("name"),
                "full_name": project_info.get("path_with_namespace"),
                "html_url": project_info.get("web_url"),
                "visibility": project_info.get("visibility"),
                "repo_metadata": {
                    "description": project_info.get("description"),
                    "language": project_info.get("language"),
                    "stars": project_info.get("star_count", 0),
                },
                "default_branch": branch,
                "sync_status": "pending",
            },
        )

        # Mark as syncing
        self.repository_repo.mark_syncing(repo.id)

        # 3. Create sync history
        sync_history = SyncHistoryModel(
            repo_id=repo.id,
            sync_type="full",
            triggered_by="manual",
            user_id=user_id,
            to_commit_sha="", # Will be set after sync
            status="running",
        )
        sync_history = self.sync_history_repo.create(sync_history)

        try:
            # 5. Get repository tree with error handling
            code_files = gitlab_service.filter_code_files(project_id=repository_external_id, ref=branch)
            # Check if HEAD commit already synced by comparing real GitLab SHA
            existing_commit = self.commit_repository.get_latest_full_sync_by_repo_id(repo.id)

            if existing_commit and existing_commit.sha == head_commit_sha:
                # Check if there are pending items for this commit
                pending_count = self.sync_queue_repo.count_pending_by_commit(existing_commit.id)

                if pending_count == 0:
                    # Mark sync as completed
                    self._complete_sync_for_repo(sync_history_id=sync_history.id, repo_id=repo.id)

                    return {
                        "success": True,
                        "repository": repo.name,
                        "repository_id": repo.id,
                        "knowledge_base_id": kb_entity.id,
                        "knowledge_base_name": kb_entity.name,
                        "commit_sha": head_commit_sha,
                        "files_processed": len(code_files),
                        "files_succeeded": len(code_files),
                        "files_failed": 0,
                        "total_embeddings": 0,
                    }
                # Resume processing existing queue
                commit = existing_commit
                    
            else:
                # Create commit with real GitLab SHA and metadata
                commit = self.commit_repository.create_with_metadata(
                    repo_id=repo.id,
                    sha=head_commit_sha,
                    external_id=head_commit_sha,
                    author_name=head_commit_info["author_name"],
                    author_email=head_commit_info["author_email"],
                    message=head_commit_info["message"],
                    committed_at=datetime.fromisoformat(head_commit_info["committed_at"].replace('Z', '+00:00')),
                    files_changed=len(code_files)
                )

            # 7. Queue all files for processing with batched insertion for large repos
            file_count = len(code_files)
            
            total_queued = 0
            for batch_start in range(0, file_count, SYNC_QUEUE_BULK_INSERT_BATCH_SIZE):
                batch_end = min(batch_start + SYNC_QUEUE_BULK_INSERT_BATCH_SIZE, file_count)
                batch_files = code_files[batch_start:batch_end]
                
                # Create file history for this batch
                file_history_batch = []
                for file_path in batch_files:
                    file_change = FileChangeHistoryModel(
                        repo_id=repo.id,
                        commit_id=commit.id,
                        sync_history_id=sync_history.id,
                        file_path=file_path,
                        change_type="added",
                        sync_status="pending",
                    )
                    file_history_batch.append(file_change)
                
                # Bulk insert file history batch
                self.file_change_repo.create_batch(file_history_batch)
                
                # Create queue items for this batch
                queue_batch = []
                for file_change in file_history_batch:
                    queue_item = SyncQueueModel(
                        repo_id=repo.id,
                        commit_id=commit.id,
                        file_change_history_id=file_change.id,
                        file_path=file_change.file_path,
                        change_type="added",
                        priority=0,  # TODO: Use SYNC_PRIORITY_* constants based on file type
                        status="pending",
                    )
                    queue_batch.append(queue_item)
                
                # Bulk insert queue batch
                self.sync_queue_repo.enqueue_batch(queue_batch)
                total_queued += len(queue_batch)

            # Update sync history with queued file count and to_commit_sha
            sync_history.files_queued = total_queued
            sync_history.to_commit_sha = commit.sha
            self.sync_history_repo.update(sync_history)
            
            # 8. Process queue in batches with connector config
            sync_config = self.connector_service.get_sync_config(gitlab_connector)
            batch_size = sync_config.get("batch_size", GITLAB_SYNC_BATCH_SIZE_DEFAULT)

            result = await self._process_queue(
                repo=repo,
                sync_history=sync_history,
                gitlab_service=gitlab_service,
                knowledge_base_id=kb_entity.id,
                persist_directory=kb_entity.vector_store_collection,
                user_id=user_id,
                branch=branch,
                batch_size=batch_size,
            )

            

            # STEP 6: KB SOURCE MANAGEMENT - BRANCH CHANGE DETECTION & CLEANUP
            existing_source = self.kb_source_repo.get_by_kb_and_source(
                kb_id=kb_entity.id,
                source_type="repository",
                source_id=str(repo.id)
            )

            if existing_source:
                await self._handle_branch_change_cleanup(existing_source, kb_entity.id, branch, repo.id)
                # Update existing source
                existing_source.sync_status = "completed"
                existing_source.auto_sync = auto_sync
                existing_source.config = {"branch": branch}
                existing_source.last_synced_at = datetime.utcnow()
                self.kb_source_repo.update_source_sync_status(existing_source)
            else:
                # Create new source
                self.kb_source_repo.create({
                    "knowledge_base_id": kb_entity.id,
                    "source_type": "repository",
                    "source_id": str(repo.id),
                    "config": {"branch": branch},
                    "auto_sync": auto_sync,
                    "sync_status": "completed",
                    "last_synced_at": datetime.utcnow()
                })

            # 9. Mark sync as completed
            self._complete_sync_for_repo(sync_history_id=sync_history.id, repo_id=repo.id)

            return {
                "success": True,
                "repository": repo.name,
                "repository_id": repo.id,
                "knowledge_base_id": kb_entity.id,
                "knowledge_base_name": kb_entity.name,
                "files_processed": result.get("files_processed", 0),
                "files_succeeded": result.get("files_succeeded", 0),
                "files_failed": result.get("files_failed", 0),
                "total_embeddings": result.get("total_embeddings", 0),
            }

        except Exception as e:
            self._fail_sync_for_repo(sync_history.id, repo.id, str(e))
            raise

    async def _fetch_file_content_async(
        self,
        gitlab_service: GitLabService,
        project_id: str,
        file_path: str,
        ref: str
    ) -> Optional[str]:
        """
        Async wrapper for fetching file content.

        Args:
            gitlab_service: GitLab service instance
            project_id: Project ID
            file_path: File path
            ref: Branch/ref name

        Returns:
            File content or None if error
        """
        try:
            # Run sync GitLab API call in executor to avoid blocking
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None,
                lambda: gitlab_service.get_file_content(project_id, file_path, ref)
            )
            return content
        except Exception as e:
            logger.error(f"Failed to fetch {file_path}: {str(e)}")
            return None

    async def _process_queue(
        self,
        repo: RepositoryModel,
        sync_history: SyncHistoryModel,
        gitlab_service: GitLabService,
        knowledge_base_id: int,
        persist_directory: str,
        user_id: int,
        branch: str,
        batch_size: int = 10,
    ) -> Dict[str, Any]:
        """
        Process queued files in batches with parallel fetching.

        Args:
            repo: Repository model
            sync_history: Sync history model
            gitlab_service: GitLab service
            knowledge_base_id: Knowledge Base ID
            user_id: User ID
            branch: Branch name
            batch_size: Number of files per batch

        Returns:
            Dictionary with processing results
        """
        total_processed = 0
        total_succeeded = 0
        total_failed = 0
        total_embeddings = 0

        while True:
            # Get next batch of pending files
            batch = self.sync_queue_repo.get_pending_batch(repo_id=repo.id, limit=batch_size)

            if not batch:
                break

            # Mark as processing
            self.sync_queue_repo.mark_processing([item.id for item in batch])

            # Fetch all files in parallel
            fetch_tasks = [
                self._fetch_file_content_async(
                    gitlab_service,
                    repo.external_id,
                    queue_item.file_path,
                    branch
                )
                for queue_item in batch
            ]
            file_contents = await asyncio.gather(*fetch_tasks, return_exceptions=True)

            # Accumulate documents for batch embedding
            all_documents = []
            file_results = []  # Track success/failure per file

            # Process each file with its fetched content
            for queue_item, content in zip(batch, file_contents):
                try:
                    start_time = datetime.utcnow()

                    # Check if content fetch failed or is exception
                    if content is None or isinstance(content, Exception):
                        error_msg = str(content) if isinstance(content, Exception) else "Failed to fetch content"
                        raise Exception(error_msg)

                    # Chunk code with proper metadata
                    repo_info = {
                        "repo": repo.name,
                        "repo_url": repo.html_url or "",
                        "branch": branch,
                        "commit": "",
                        "author": "System",
                    }
                    metadata = self.code_chunking_service.extract_metadata(
                        file_path=queue_item.file_path, content=content, repo_info=repo_info
                    )
                    chunks = self.code_chunking_service.chunk_code(
                        file_path=queue_item.file_path, content=content, metadata=metadata
                    )

                    # Create documents
                    documents = []
                    for chunk in chunks:
                        doc_metadata = {
                            **chunk.metadata,
                            "source": "gitlab",
                            "repository": repo.full_name or repo.name,
                            "knowledge_base_id": knowledge_base_id,
                            "user_id": user_id,
                        }
                        documents.append({"content": chunk.text, "metadata": doc_metadata})

                    # Accumulate for batch processing
                    all_documents.extend(documents)

                    process_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                    # Track successful processing
                    file_results.append({
                        "queue_item": queue_item,
                        "status": "success",
                        "chunks": len(chunks),
                        "process_time": process_time
                    })

                except Exception as e:
                    logger.error(f"Failed to process {queue_item.file_path}: {str(e)}")
                    file_results.append({
                        "queue_item": queue_item,
                        "status": "failed",
                        "error": str(e)
                    })

            # Batch sync all documents to vector store at once
            if all_documents:
                try:
                    logger.info(f"Batch syncing {len(all_documents)} documents from {len(batch)} files")
                    await self.kb_sync_service.sync_documents(all_documents, persist_directory)
                except Exception as e:
                    logger.error(f"Batch embedding failed: {str(e)}")
                    # Mark all as failed if batch embedding fails
                    for result in file_results:
                        if result["status"] == "success":
                            result["status"] = "failed"
                            result["error"] = f"Batch embedding failed: {str(e)}"

            # Update database with results
            for result in file_results:
                queue_item = result["queue_item"]

                if result["status"] == "success":
                    self.sync_queue_repo.mark_completed(queue_item.id)
                    self.file_change_repo.mark_synced(
                        queue_item.file_change_history_id, result["process_time"]
                    )
                    total_succeeded += 1
                    total_embeddings += result["chunks"]
                else:
                    self.sync_queue_repo.mark_failed(queue_item.id, result["error"])
                    self.file_change_repo.mark_failed(
                        queue_item.file_change_history_id, "processing_error", result["error"]
                    )
                    total_failed += 1

                total_processed += 1

            # Update sync history stats
            self.sync_history_repo.increment_stats(
                sync_history.id,
                files_processed=len(batch),
                files_succeeded=total_succeeded,
                files_failed=total_failed,
                embeddings_created=total_embeddings,
                batches_completed=1,
            )

        # Return final results after all batches processed
        return {
            "success": True,
            "repository": repo.name,
            "files_processed": total_processed,
            "files_succeeded": total_succeeded,
            "files_failed": total_failed,
            "total_embeddings": total_embeddings,
        }

    async def _handle_branch_change_cleanup(self, source: KnowledgeBaseSourceModel, kb_id: int, branch: str, repo_id: int):
        """
        Detect branch change and cleanup old branch vectors if needed.
        Raises VectorCleanupException if cleanup fails.
        """
        old_branch = source.config.get("branch")

        # BRANCH CHANGE DETECTION & CLEANUP
        if old_branch and old_branch != branch:
            # CLEANUP OLD BRANCH VECTORS
            cleanup_result = await self.kb_cleanup_service.cleanup_branch_change(
                kb_id=kb_id,
                source_id=str(source.id),
                old_branch=old_branch
            )

            if not cleanup_result["success"]:
                # CLEANUP FAILED - ABORT SYNC
                raise VectorCleanupException(
                    message=cleanup_result.get('error', 'Unknown error during branch cleanup'),
                    details={
                        "kb_id": kb_id,
                        "source_id": str(source.id),
                        "old_branch": old_branch,
                        "new_branch": branch,
                        "repo_id": repo_id
                    }
                )
            logger.info(f"Successfully cleaned up {cleanup_result['deleted_vectors']} vectors from old branch '{old_branch}'")

    def _complete_sync_for_repo(self, sync_history_id: int, repo_id: int, status: str = "completed"):
        """
            mark the sync history and repository as completed.

            Args:
                sync_history_id: ID of the sync history record
                repo_id: ID of the repository
                status: Sync status, default "completed"
        """
        try:
            self.sync_history_repo.complete_sync(sync_history_id, status)
            self.repository_repo.mark_completed(repo_id)
        except Exception as status_error:
            logger.error(f"Failed to update completed sync status: {status_error}")
            raise

    def _fail_sync_for_repo(self, sync_history_id: int, repo_id: int, message: str, status: str = "failed"):
        """
            mark the sync history and repository as failed.

            Args:
                sync_history_id: ID of the sync history record
                repo_id: ID of the repository
                message: Failure message
                status: Sync status, default "failed"
        """
        try:
            self.sync_history_repo.complete_sync(sync_history_id, status, message)
            self.repository_repo.mark_failed(repo_id)
        except Exception as status_error:
            logger.error(f"Failed to update failed sync status: {status_error}")
            raise
