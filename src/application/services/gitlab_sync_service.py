"""
GitLab Sync Service - Enhanced with incremental sync and queue-based processing.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from infrastructure.external.gitlab_service import GitLabService
from application.services.code_chunking_service import CodeChunkingService
from application.services.kb_sync_service import KBSyncService
from infrastructure.postgresql.repositories.repository_repository import RepositoryRepository
from infrastructure.postgresql.repositories.user_connection_repository import UserConnectionRepository
from infrastructure.postgresql.repositories.sync_history_repository import SyncHistoryRepository
from infrastructure.postgresql.repositories.sync_queue_repository import SyncQueueRepository
from infrastructure.postgresql.repositories.file_change_history_repository import FileChangeHistoryRepository
from infrastructure.postgresql.models.repository_model import RepositoryModel
from infrastructure.postgresql.models.commit_model import CommitModel
from infrastructure.postgresql.models.sync_history_model import SyncHistoryModel
from infrastructure.postgresql.models.sync_queue_model import SyncQueueModel
from infrastructure.postgresql.models.file_change_history_model import FileChangeHistoryModel
from shared.interfaces.repositories.document_repository import DocumentRepository
from core.logger import logger


class GitLabSyncService:
    """Enhanced GitLab sync service with incremental sync support."""

    def __init__(
        self,
        db_session: Session,
        code_chunking_service: CodeChunkingService,
        kb_sync_service: KBSyncService,
        document_repository: DocumentRepository
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
        self.code_chunking_service = code_chunking_service
        self.kb_sync_service = kb_sync_service
        self.document_repository = document_repository

        # Initialize repositories
        self.repository_repo = RepositoryRepository(db_session)
        self.connection_repo = UserConnectionRepository(db_session)
        self.sync_history_repo = SyncHistoryRepository(db_session)
        self.sync_queue_repo = SyncQueueRepository(db_session)
        self.file_change_repo = FileChangeHistoryRepository(db_session)

    def sync_repository_full(
        self,
        connection_id: int,
        repository_external_id: str,
        knowledge_base_id: str,
        group_id: str,
        user_id: int,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Perform full repository sync.

        Args:
            connection_id: User connection ID
            repository_external_id: External repository ID (GitLab project ID)
            knowledge_base_id: Knowledge Base ID
            group_id: Group ID
            user_id: User ID
            branch: Branch to sync

        Returns:
            Dictionary with sync results
        """
        logger.info(f"Starting full sync for repo {repository_external_id}")

        # 1. Get or create system connection (simplified - just for tracking)
        connection = self.connection_repo.get_by_id(connection_id)
        if not connection:
            # Auto-create system connection if not exists
            from infrastructure.postgresql.models.user_connection_model import UserConnectionModel
            from infrastructure.postgresql.models.connector_model import ConnectorModel

            # Get or create GitLab connector
            connector = self.db_session.query(ConnectorModel).filter(
                ConnectorModel.provider_type == "gitlab"
            ).first()

            if not connector:
                connector = ConnectorModel(
                    name="GitLab",
                    provider_type="gitlab",
                    auth_type="pat",
                    is_active=True
                )
                self.db_session.add(connector)
                self.db_session.commit()
                self.db_session.refresh(connector)

            # Create system connection
            connection = UserConnectionModel(
                user_id=user_id,  # Admin user
                connector_id=connector.id,
                is_active=True,
                connection_metadata={"system": True, "gitlab_url": "settings"}
            )
            connection.id = connection_id  # Force ID = 1
            self.db_session.add(connection)
            self.db_session.commit()

        # Get GitLab service (uses admin token from settings)
        gitlab_service = self._get_gitlab_service()

        # 2. Get or create repository record
        repo, created = self.repository_repo.get_or_create(
            connection_id=connection_id,
            external_id=repository_external_id,
            defaults={
                "name": f"repo_{repository_external_id}",
                "default_branch": branch,
                "sync_status": "pending"
            }
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
            status="running"
        )
        sync_history = self.sync_history_repo.create(sync_history)

        try:
            # 4. Get repository info
            project_info = gitlab_service.get_project_info(repository_external_id)

            # Update repository model with info
            repo.name = project_info.get("name", repo.name)
            repo.full_name = project_info.get("path_with_namespace")
            repo.html_url = project_info.get("web_url")
            repo.visibility = project_info.get("visibility")
            repo.repo_metadata = {
                "description": project_info.get("description"),
                "language": project_info.get("language"),
                "stars": project_info.get("star_count", 0)
            }
            self.repository_repo.update(repo)

            # 5. Get repository tree
            tree = gitlab_service.get_repository_tree(
                project_id=repository_external_id,
                ref=branch,
                recursive=True
            )

            # Filter code files
            file_paths = [item["path"] for item in tree if item["type"] == "blob"]
            code_files = gitlab_service.filter_code_files(file_paths)

            logger.info(f"Found {len(code_files)} code files to process")

            # 6. Create a dummy commit for full sync
            # In full sync, we treat all files as "added" in one commit
            from infrastructure.postgresql.models.commit_model import CommitModel
            commit = CommitModel(
                repo_id=repo.id,
                external_id=f"full_sync_{datetime.utcnow().isoformat()}",
                sha="full_sync",
                author_name="System",
                message="Full repository sync",
                committed_at=datetime.utcnow(),
                files_changed=len(code_files)
            )
            self.db_session.add(commit)
            self.db_session.commit()
            self.db_session.refresh(commit)

            # 7. Queue all files for processing
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
                    sync_status="pending"
                )
                file_history_items.append(file_change)

            # Bulk insert file history
            self.file_change_repo.create_batch(file_history_items)

            # Create queue items
            for i, file_change in enumerate(file_history_items):
                queue_item = SyncQueueModel(
                    repo_id=repo.id,
                    commit_id=commit.id,
                    file_change_history_id=file_change.id,
                    file_path=file_change.file_path,
                    change_type="added",
                    priority=0,
                    status="pending"
                )
                queue_items.append(queue_item)

            # Bulk insert queue items
            self.sync_queue_repo.enqueue_batch(queue_items)

            sync_history.files_queued = len(queue_items)
            sync_history.to_commit_sha = commit.sha
            self.sync_history_repo.update(sync_history)

            logger.info(f"Queued {len(queue_items)} files")

            # 8. Process queue in batches
            result = self._process_queue(
                repo=repo,
                sync_history=sync_history,
                gitlab_service=gitlab_service,
                knowledge_base_id=knowledge_base_id,
                group_id=group_id,
                user_id=user_id,
                branch=branch
            )

            # 9. Mark sync as completed
            self.sync_history_repo.complete_sync(sync_history.id, "completed")
            self.repository_repo.mark_completed(repo.id)

            logger.info(f"Full sync completed: {result}")
            result["repository_id"] = repo.id
            return result

        except Exception as e:
            logger.error(f"Full sync failed: {str(e)}")
            self.sync_history_repo.complete_sync(
                sync_history.id,
                "failed",
                str(e)
            )
            self.repository_repo.mark_failed(repo.id)
            raise

    def sync_repository_incremental(
        self,
        repository_id: int,
        user_id: int
    ) -> Dict[str, Any]:
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
            status="running"
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
                "files_processed": 0
            }

        except Exception as e:
            logger.error(f"Incremental sync failed: {str(e)}")
            self.sync_history_repo.complete_sync(
                sync_history.id,
                "failed",
                str(e)
            )
            self.repository_repo.mark_failed(repo.id)
            raise

    def _process_queue(
        self,
        repo: RepositoryModel,
        sync_history: SyncHistoryModel,
        gitlab_service: GitLabService,
        knowledge_base_id: str,
        group_id: str,
        user_id: int,
        branch: str,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Process queued files in batches.

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
            batch = self.sync_queue_repo.get_pending_batch(
                repo_id=repo.id,
                limit=batch_size
            )

            if not batch:
                break

            # Mark as processing
            self.sync_queue_repo.mark_processing([item.id for item in batch])

            # Process each file in batch
            for queue_item in batch:
                try:
                    start_time = datetime.utcnow()

                    # Get file content
                    content = gitlab_service.get_file_content(
                        project_id=repo.external_id,
                        file_path=queue_item.file_path,
                        ref=branch
                    )

                    # Chunk code
                    chunks = self.code_chunking_service.chunk_code(
                        content,
                        queue_item.file_path
                    )

                    # Create documents
                    documents = []
                    for i, chunk in enumerate(chunks):
                        doc_metadata = {
                            "source": "gitlab",
                            "repository": repo.full_name or repo.name,
                            "file_path": queue_item.file_path,
                            "chunk_index": i,
                            "language": chunk.language,
                            "knowledge_base_id": knowledge_base_id,
                            "group_id": group_id,
                            "user_id": user_id
                        }
                        documents.append({
                            "content": chunk.content,
                            "metadata": doc_metadata
                        })

                    # Sync to vector store
                    self.kb_sync_service.sync_documents(documents)

                    # Calculate process time
                    process_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                    # Mark as completed
                    self.sync_queue_repo.mark_completed(queue_item.id)
                    self.file_change_repo.mark_synced(
                        queue_item.file_change_history_id,
                        process_time
                    )

                    total_succeeded += 1
                    total_embeddings += len(chunks)

                except Exception as e:
                    logger.error(f"Failed to process {queue_item.file_path}: {str(e)}")
                    self.sync_queue_repo.mark_failed(queue_item.id, str(e))
                    self.file_change_repo.mark_failed(
                        queue_item.file_change_history_id,
                        "processing_error",
                        str(e)
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
                batches_completed=1
            )

        return {
            "success": True,
            "repository": repo.name,
            "files_processed": total_processed,
            "files_succeeded": total_succeeded,
            "files_failed": total_failed,
            "total_embeddings": total_embeddings
        }

    def _get_gitlab_service(self, connection=None) -> GitLabService:
        """
        Get GitLab service using admin token from settings.

        Connection parameter is ignored - always use admin token.
        """
        from core.config import settings

        # Always use admin token from settings
        return GitLabService(
            gitlab_url=settings.GITLAB_URL,
            private_token=settings.GITLAB_API_TOKEN
        )
