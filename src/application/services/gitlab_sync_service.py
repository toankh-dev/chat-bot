"""
GitLab Sync Service - Enhanced with incremental sync and queue-based processing.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import select
import asyncio

from infrastructure.external.gitlab_service import GitLabService
from application.services.code_chunking_service import CodeChunkingService
from application.services.kb_sync_service import KBSyncService
from application.services.connector_service import ConnectorService
from infrastructure.postgresql.repositories.repository_repository import RepositoryRepository
from infrastructure.postgresql.repositories.user_connection_repository import (
    UserConnectionRepository,
)
from infrastructure.postgresql.repositories.sync_history_repository import SyncHistoryRepository
from infrastructure.postgresql.repositories.sync_queue_repository import SyncQueueRepository
from infrastructure.postgresql.repositories.file_change_history_repository import (
    FileChangeHistoryRepository,
)
from infrastructure.postgresql.repositories.commit_model_repository import CommitRepository
from infrastructure.postgresql.models.repository_model import RepositoryModel
from infrastructure.postgresql.models.sync_history_model import SyncHistoryModel
from infrastructure.postgresql.models.sync_queue_model import SyncQueueModel
from infrastructure.postgresql.models.file_change_history_model import FileChangeHistoryModel
from infrastructure.postgresql.models.knowledge_base_model import KnowledgeBaseModel
from infrastructure.postgresql.models.knowledge_base_source_model import KnowledgeBaseSourceModel
from shared.interfaces.repositories.document_repository import DocumentRepository
from core.logger import logger


class GitLabSyncService:
    """Enhanced GitLab sync service with incremental sync support."""

    def __init__(
        self,
        db_session: Session,
        repository_repository: RepositoryRepository,
        document_repository: DocumentRepository,
        commit_repository: CommitRepository,
        kb_sync_service: KBSyncService,
        code_chunking_service: CodeChunkingService,
        connector_service: ConnectorService,
    ):
        """
        Initialize GitLab sync service.

        Args:
            db_session: SQLAlchemy database session
            code_chunking_service: Code chunking service
            kb_sync_service: Knowledge Base sync service
            document_repository: Document repository
        """
        self.db_session = db_session
        self.repository_repository = repository_repository
        self.commit_repository = commit_repository
        self.document_repository = document_repository
        self.kb_sync_service = kb_sync_service
        self.code_chunking_service = code_chunking_service

        # Initialize repositories
        self.repository_repo = RepositoryRepository(db_session)
        self.connection_repo = UserConnectionRepository(db_session)
        self.sync_history_repo = SyncHistoryRepository(db_session)
        self.sync_queue_repo = SyncQueueRepository(db_session)
        self.file_change_repo = FileChangeHistoryRepository(db_session)
        # Initialize connector service
        self.connector_service = connector_service

    async def sync_repository_full(
        self,
        user_id: int,
        connector_id: int,
        repository_external_id: str,
        chatbot_id: int,
        branch: Optional[str] = None,
        auto_sync: bool = False,
    ) -> Dict[str, Any]:
        """
        Perform full repository sync.

        Args:
            repository_external_id: External repository ID (GitLab project ID)
            knowledge_base_id: Knowledge Base ID
            group_id: Group ID
            user_id: User ID
            branch: Branch to sync

        Returns:
            Dictionary with sync results
        """
        # Step 1: Get GitLab service
        gitlab_connector = self.connector_service.get_connector_by_id(connector_id)
        if not gitlab_connector:
            raise ValueError("GitLab connector not configured")

        gitlab_service = self.connector_service.get_gitlab_service(gitlab_connector)

        # 2. Get or create system connection properly
        connection = self.connector_service.get_or_create_system_connection(
            user_id=user_id, connector=gitlab_connector
        )

        # Step 3: Fetch repository information
        project_info = gitlab_service.get_project_info(repository_external_id)
        repository_external_id = str(project_info["id"])
        repo_name = project_info["name"]
        branch = branch if branch else project_info.get("default_branch", "main")

        # Step 4: Create/get Knowledge Base (sync version)
        kb_name = f"{repo_name} Knowledge Base"

        # Try to find existing KB using sync session
        stmt = select(KnowledgeBaseModel).where(
            KnowledgeBaseModel.name == kb_name,
            KnowledgeBaseModel.chatbot_id == chatbot_id
        )
        existing_kb = self.db_session.execute(stmt).scalar_one_or_none()

        if existing_kb:
            kb_entity = existing_kb
        else:
            # Create new KB
            kb_entity = KnowledgeBaseModel(
                chatbot_id=chatbot_id,
                name=kb_name,
                description=f"Knowledge base for {repo_name} repository",
                vector_store_type="chromadb",
                vector_store_collection=f"kb_{chatbot_id}_{repo_name.lower().replace(' ', '_')}",
                is_active=True
            )
            self.db_session.add(kb_entity)
            self.db_session.flush()
            self.db_session.refresh(kb_entity)

        knowledge_base_id = kb_entity.vector_store_collection or f"kb_{kb_entity.id}"
        group_id = f"group_gitlab_{repository_external_id}"

        # 2. Get or create repository record
        repo, created = self.repository_repo.get_or_create(
            connection_id=connection.id,
            external_id=repository_external_id,
            defaults={
                "name": f"repo_{repository_external_id}",
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
            to_commit_sha="",  # Will update later
            status="running",
        )
        sync_history = self.sync_history_repo.create(sync_history)

        try:
            # Update repository model with info (without committing yet)
            repo.name = project_info.get("name", repo.name)
            repo.full_name = project_info.get("path_with_namespace")
            repo.html_url = project_info.get("web_url")
            repo.visibility = project_info.get("visibility")
            repo.repo_metadata = {
                "description": project_info.get("description"),
                "language": project_info.get("language"),
                "stars": project_info.get("star_count", 0),
            }
            # Don't commit yet - will be part of larger transaction
            repo.updated_at = datetime.utcnow()

            # 5. Get repository tree
            tree = gitlab_service.get_repository_tree(
                project_id=repository_external_id, ref=branch, recursive=True
            )

            # Filter code files
            file_paths = [item["path"] for item in tree if item["type"] == "blob"]
            code_files = gitlab_service.filter_code_files(file_paths)

            # Get or create commit using database repo.id (NOT external_id)
            existing_commit = self.commit_repository.get_latest_full_sync_by_repo_id(repo.id)

            if existing_commit:
                # Commit already exists - check if already processed
                logger.info(f"Found existing commit {existing_commit.id} for repo {repo.id}")

                # Check if there are pending items for this commit
                pending_count = self.sync_queue_repo.count_pending_by_commit(existing_commit.id)

                if pending_count > 0:
                    # Resume processing existing queue
                    logger.info(f"Resuming {pending_count} pending files from previous sync")
                    commit = existing_commit
                else:
                    # All files already processed - skip queuing
                    logger.info(f"All files already synced for commit {existing_commit.id}, skipping")

                    # Mark sync as completed
                    self.sync_history_repo.complete_sync(sync_history.id, "completed")
                    self.repository_repo.mark_completed(repo.id)

                    # Link repository to chatbot
                    repo.chatbot_id = chatbot_id
                    self.db_session.commit()

                    return {
                        "success": True,
                        "repository": repo_name,
                        "repository_id": repo.id,
                        "knowledge_base_id": kb_entity.id,
                        "knowledge_base_name": kb_entity.name,
                        "files_processed": len(code_files),
                        "files_succeeded": len(code_files),
                        "files_failed": 0,
                        "total_embeddings": 0,
                        "message": "Repository already synced, skipped processing"
                    }
            else:
                # Create new commit
                commit = self.commit_repository.create(repo.id, code_files)
                logger.info(f"Created new commit {commit.id} for repo {repo.id}")

            # 7. Queue all files for processing (only for new commits or resumed syncs)
            queue_items = []
            file_history_items = []

            for file_path in code_files:
                # Create file change history
                file_change = FileChangeHistoryModel(
                    repo_id=repo.id,
                    commit_id=commit.id,
                    sync_history_id=sync_history.id,
                    file_path=file_path,
                    change_type="added",
                    sync_status="pending",
                )
                file_history_items.append(file_change)

            # Bulk insert file history
            self.file_change_repo.create_batch(file_history_items)

            # Refresh file_history_items to get IDs after bulk insert
            for file_change in file_history_items:
                self.db_session.refresh(file_change)

            # Create queue items
            for i, file_change in enumerate(file_history_items):
                queue_item = SyncQueueModel(
                    repo_id=repo.id,
                    commit_id=commit.id,
                    file_change_history_id=file_change.id,
                    file_path=file_change.file_path,
                    change_type="added",
                    priority=0,
                    status="pending",
                )
                queue_items.append(queue_item)

            # Bulk insert queue items
            self.sync_queue_repo.enqueue_batch(queue_items)

            sync_history.files_queued = len(queue_items)
            sync_history.to_commit_sha = commit.sha
            self.sync_history_repo.update(sync_history)

            # 8. Process queue in batches with connector config
            sync_config = self.connector_service.get_sync_config(gitlab_connector)
            batch_size = sync_config.get("batch_size", 50)  # Increased from 10 to 50 for better performance

            result = await self._process_queue(
                repo=repo,
                sync_history=sync_history,
                gitlab_service=gitlab_service,
                knowledge_base_id=knowledge_base_id,
                group_id=group_id,
                user_id=user_id,
                branch=branch,
                batch_size=batch_size,
            )

            # 9. Mark sync as completed
            self.sync_history_repo.complete_sync(sync_history.id, "completed")
            self.repository_repo.mark_completed(repo.id)

            repository_db_id = repo.id

            # Add repository source (sync version)
            # Check if source already exists
            source_stmt = select(KnowledgeBaseSourceModel).where(
                KnowledgeBaseSourceModel.knowledge_base_id == kb_entity.id,
                KnowledgeBaseSourceModel.source_type == "repository",
                KnowledgeBaseSourceModel.source_id == str(repository_db_id)
            )
            existing_source = self.db_session.execute(source_stmt).scalar_one_or_none()

            if existing_source:
                # Update existing source
                existing_source.sync_status = "completed"
                existing_source.auto_sync = auto_sync
                existing_source.config = {"branch": branch}
                existing_source.last_synced_at = datetime.utcnow()
                kb_source = existing_source
            else:
                # Create new source
                kb_source = KnowledgeBaseSourceModel(
                    knowledge_base_id=kb_entity.id,
                    source_type="repository",
                    source_id=str(repository_db_id),
                    config={"branch": branch},
                    auto_sync=auto_sync,
                    sync_status="completed",
                    last_synced_at=datetime.utcnow()
                )
                self.db_session.add(kb_source)
                self.db_session.flush()

            # Link repository to chatbot
            repo.chatbot_id = chatbot_id

            # Commit all changes in one transaction
            self.db_session.commit()
            logger.info(f"Successfully synced repository {repo_name} (ID: {repository_db_id})")

            return {
                "success": True,
                "repository": repo_name,
                "repository_id": repository_db_id,
                "knowledge_base_id": kb_entity.id,
                "knowledge_base_name": kb_entity.name,
                "files_processed": result.get("files_processed", 0),
                "files_succeeded": result.get("files_succeeded", 0),
                "files_failed": result.get("files_failed", 0),
                "total_embeddings": result.get("total_embeddings", 0),
            }

        except Exception as e:
            logger.error(f"Full sync failed: {str(e)}")
            # Rollback all changes in transaction
            try:
                self.db_session.rollback()
            except Exception as rollback_error:
                logger.error(f"Failed to rollback session: {rollback_error}")

            # Update sync status
            try:
                self.sync_history_repo.complete_sync(sync_history.id, "failed", str(e))
                self.repository_repo.mark_failed(repo.id)
            except Exception as status_error:
                logger.error(f"Failed to update sync status: {status_error}")

            raise

    async def sync_repository_incremental(self, repository_id: int, user_id: int) -> Dict[str, Any]:
        """
        Perform incremental repository sync (only new commits).

        Args:
            repository_id: Repository ID
            user_id: User ID

        Returns:
            Dictionary with sync results
        """
        logger.info(f"Starting incremental sync for repo {repository_id}")

        # 1. Get repository
        repo = self.repository_repo.get_by_id(repository_id)
        if not repo:
            raise ValueError(f"Repository {repository_id} not found")

        # Get GitLab service (uses admin token from settings)
        gitlab_service = self._get_gitlab_service()

        # 2. Get latest sync
        latest_sync = self.sync_history_repo.get_latest_sync(repo.id)
        if not latest_sync:
            raise ValueError("No previous sync found. Please run full sync first.")

        # Mark as syncing
        self.repository_repo.mark_syncing(repo.id)

        # 3. Create sync history
        sync_history = SyncHistoryModel(
            repo_id=repo.id,
            sync_type="incremental",
            triggered_by="manual",
            user_id=user_id,
            from_commit_sha=latest_sync.to_commit_sha,
            to_commit_sha="",  # Will update later
            status="running",
        )
        sync_history = self.sync_history_repo.create(sync_history)

        try:
            # 4. TODO: Fetch new commits from GitLab API
            # For now, just mark as completed with no changes
            logger.info("Incremental sync: No new commits found")

            self.sync_history_repo.complete_sync(sync_history.id, "completed")
            self.repository_repo.mark_completed(repo.id)

            return {
                "success": True,
                "sync_type": "incremental",
                "new_commits": 0,
                "files_processed": 0,
            }

        except Exception as e:
            logger.error(f"Incremental sync failed: {str(e)}")
            self.sync_history_repo.complete_sync(sync_history.id, "failed", str(e))
            self.repository_repo.mark_failed(repo.id)
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
        knowledge_base_id: str,
        group_id: str,
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
            group_id: Group ID
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
            logger.info(f"Fetching {len(batch)} files in parallel...")
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
                            "group_id": group_id,
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
                    await self.kb_sync_service.sync_documents(all_documents)
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
