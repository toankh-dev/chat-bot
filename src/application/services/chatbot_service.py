"""
ChatbotEntity service.

Handles chatbot management business logic.
"""

from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from infrastructure.postgresql.models import ChatbotModel
from core.errors import NotFoundError, ValidationError
from domain.entities.user import UserEntity
from domain.entities.chatbot import ChatbotEntity
from shared.interfaces.repositories.chatbot_repository import ChatbotRepository
from shared.interfaces.repositories.group_chatbot_repository import GroupChatbotRepository
from shared.interfaces.repositories.group_repository import GroupRepository
from shared.interfaces.repositories.user_chatbot_repository import UserChatbotRepository
from shared.interfaces.repositories.user_repository import UserRepository



class ChatbotService:
    """
    Service for chatbot management operations.
    Works exclusively with domain entities, not ORM models.
    """

    def __init__(
        self,
        chatbot_repository: ChatbotRepository,
        group_chatbot_repository: Optional[GroupChatbotRepository] = None,
        user_chatbot_repository: Optional[UserChatbotRepository] = None,
        group_repository: Optional[GroupRepository] = None,
        user_repository: Optional[UserRepository] = None
    ):
        self.chatbot_repository = chatbot_repository
        self.group_chatbot_repository = group_chatbot_repository
        self.user_chatbot_repository = user_chatbot_repository
        self.group_repository = group_repository
        self.user_repository = user_repository

    async def get_chatbot_assigned_groups(self, chatbot_id: int):
        """Get groups assigned to a chatbot."""
        if not self.group_chatbot_repository:
            return []
        return await self.group_chatbot_repository.get_chatbot_groups(chatbot_id)

    async def get_chatbot_assigned_users(self, chatbot_id: int) -> List[UserEntity]:
        """Get users assigned to a chatbot."""
        if not self.user_chatbot_repository or not self.user_repository:
            return []

        user_ids = await self.user_chatbot_repository.get_chatbot_users(chatbot_id)
        users = []
        for user_id in user_ids:
            user = await self.user_repository.find_by_id(user_id)
            if user:
                users.append(user)
        return users

    async def get_chatbot_by_id(self, chatbot_id: int, include_assignments: bool = False) -> ChatbotEntity:
        """
        Get chatbot by ID.

        Args:
            chatbot_id: Chatbot ID (integer)
            include_assignments: Whether to load assigned groups and users

        Returns:
            Chatbot: Found chatbot

        Raises:
            NotFoundError: If chatbot not found
        """
        chatbot = await self.chatbot_repository.find_by_id(chatbot_id)
        if not chatbot:
            raise NotFoundError(f"Chatbot with ID {chatbot_id} not found")

        # Load assignments if requested
        if include_assignments:
            chatbot.assigned_groups = await self.get_chatbot_assigned_groups(chatbot_id)
            chatbot.assigned_users = await self.get_chatbot_assigned_users(chatbot_id)

        return chatbot
    
    async def get_chatbot_model_data(self, chatbot_id: int) -> dict:
        """
        Get chatbot model data with all fields from database.

        This is a helper method to get the full model data including
        fields not in the domain entity (model_id, top_p, etc.)

        Args:
            chatbot_id: Chatbot ID (integer)

        Returns:
            Dictionary with all chatbot model fields

        Raises:
            NotFoundError: If chatbot not found
        """
        from sqlalchemy import select
        from infrastructure.postgresql.models import ChatbotModel

        # Access the session from repository to query model directly
        if hasattr(self.chatbot_repository, 'session'):
            result = await self.chatbot_repository.session.execute(
                select(ChatbotModel)
                .options(selectinload(ChatbotModel.ai_model))
                .where(ChatbotModel.id == chatbot_id)
            )
            model = result.scalar_one_or_none()
            if model:
                # Get model name from relationship
                if not model.ai_model:
                    raise NotFoundError(f"AI model with ID {model.model_id} not found for chatbot {chatbot_id}")
                model_name = model.ai_model.name
                return {
                    "id": model.id,
                    "model_id": model.model_id,
                    "model_name": model_name,
                    "top_p": model.top_p,
                    "welcome_message": model.welcome_message,
                    "fallback_message": model.fallback_message,
                    "max_conversation_length": model.max_conversation_length,
                    "enable_function_calling": model.enable_function_calling,
                    "created_by": model.created_by,
                    "status": model.status
                }

        raise NotFoundError(f"Chatbot model with ID {chatbot_id} not found")

    async def get_chatbot_creator(self, created_by_id: int) -> Optional[UserEntity]:
        """
        Get the user who created the chatbot.

        Args:
            created_by_id: User ID of creator

        Returns:
            UserEntity or None if not found
        """
        if not self.user_repository:
            return None

        return await self.user_repository.find_by_id(created_by_id)

    async def list_chatbots(self, skip: int = 0, limit: int = 100) -> List[ChatbotEntity]:
        """
        List all chatbots with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Chatbot]: List of chatbots
        """
        return await self.chatbot_repository.find_all(skip=skip, limit=limit)

    async def list_active_chatbots(self, skip: int = 0, limit: int = 100) -> List[ChatbotEntity]:
        """
        List active chatbots with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Chatbot]: List of active chatbots
        """
        return await self.chatbot_repository.find_active_chatbots(skip=skip, limit=limit)

    async def create_chatbot(
        self,
        workspace_id: int,
        name: str,
        model_id: int,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Decimal = Decimal("0.7"),
        max_tokens: int = 2048,
        tools: List[str] = [],
        group_ids: Optional[List[int]] = None,
        user_ids: Optional[List[int]] = None,
        assigned_by: Optional[int] = None,
        top_p: Decimal = Decimal("1.0"),
        welcome_message: Optional[str] = None,
        fallback_message: Optional[str] = None,
        max_conversation_length: int = 50,
        enable_function_calling: bool = True,
        created_by: Optional[int] = None
    ) -> ChatbotEntity:
        """
        Create new chatbot.

        Args:
            name: Chatbot name
            model_id: Model identifier
            description: Chatbot description
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum response tokens
            system_prompt: System instructions
            welcome_message: Initial message
            fallback_message: Error fallback message
            max_conversation_length: Context window size
            enable_function_calling: Enable tool use
            group_ids: Optional list of group IDs to assign chatbot to
            user_ids: Optional list of user IDs to assign chatbot to
            assigned_by: Admin ID who is making the assignments
            created_by: User ID who created the chatbot (defaults to assigned_by if not provided)

        Returns:
            Chatbot: Created chatbot

        """
        # Validate group IDs if provided
        if group_ids:
            if not assigned_by:
                raise ValidationError("assigned_by is required when assigning to groups")
            if self.group_repository:
                for group_id in group_ids:
                    if not await self.group_repository.exists(group_id):
                        raise ValidationError(f"Group with ID {group_id} not found")

        # Validate user IDs if provided
        if user_ids:
            if not assigned_by:
                raise ValidationError("assigned_by is required when assigning to users")
            if self.user_repository:
                for user_id in user_ids:
                    if not await self.user_repository.exists(user_id):
                        raise ValidationError(f"User with ID {user_id} not found")

        # Use created_by if provided, otherwise fall back to assigned_by
        creator_id = created_by if created_by is not None else assigned_by
        if not creator_id:
            raise ValidationError("Either created_by or assigned_by is required to create a chatbot")
        
        # Create entity with temporary ID (will be replaced by database)
        chatbot = ChatbotEntity(
            id=0,  # Temporary ID, will be set by database
            name=name,
            description=description or "",
            system_prompt=system_prompt or "",
            model_id=model_id,
            temperature=float(temperature),
            max_tokens=max_tokens,
            top_p=float(top_p),
            welcome_message=welcome_message or "",
            fallback_message=fallback_message or "",
            max_conversation_length=max_conversation_length,
            enable_function_calling=enable_function_calling,
            created_by=creator_id,
        )
        
        created_chatbot = await self.chatbot_repository.create(
            chatbot,
            created_by=creator_id,
            model_id=model_id,
            top_p=top_p,
            welcome_message=welcome_message,
            fallback_message=fallback_message,
            max_conversation_length=max_conversation_length,
            enable_function_calling=enable_function_calling
        )

        # Assign to groups if provided
        if group_ids and self.group_chatbot_repository:
            await self.group_chatbot_repository.assign_chatbot_to_groups(
                chatbot_id=created_chatbot.id,
                group_ids=group_ids,
                assigned_by=assigned_by
            )

        # Assign to users if provided
        if user_ids and self.user_chatbot_repository:
            await self.user_chatbot_repository.assign_chatbot_to_users(
                chatbot_id=created_chatbot.id,
                user_ids=user_ids,
                assigned_by=assigned_by
            )

        return created_chatbot

    async def update_chatbot(
        self,
        chatbot_id: int,
        workspace_id: int,
        name: str,
        model_id: Optional[int] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Decimal = Decimal("0.7"),
        max_tokens: int = 2048,
        tools: List[str] = [],
        is_active: Optional[bool] = None,
        group_ids: Optional[List[int]] = None,
        user_ids: Optional[List[int]] = None,
        assigned_by: Optional[int] = None,
        top_p: Optional[Decimal] = None,
        welcome_message: Optional[str] = None,
        fallback_message: Optional[str] = None,
        max_conversation_length: Optional[int] = None,
        enable_function_calling: Optional[bool] = None
    ) -> ChatbotEntity:
        """
        Update chatbot configuration.

        Args:
            chatbot_id: Chatbot ID (integer)
            workspace_id: Workspace ID (integer)
            name: New name
            model_id: Model identifier
            description: New description (optional)
            system_prompt: New system prompt (optional)
            temperature: New temperature (optional)
            max_tokens: New max tokens (optional)
            tools: List of tools (optional)
            is_active: Active status (optional)
            group_ids: New list of group IDs (replaces existing, optional)
            user_ids: New list of user IDs (replaces existing, optional)
            assigned_by: Admin ID who is making the assignments
            model_id: AI model ID (optional, preserves existing if not provided)
            top_p: Top-p sampling parameter (optional)
            welcome_message: New welcome message (optional)
            fallback_message: New fallback message (optional)
            max_conversation_length: New context window (optional)
            enable_function_calling: Enable/disable tools (optional)

        Returns:
            Chatbot: Updated chatbot domain entity

        Raises:
            NotFoundError: If chatbot not found
        """
        chatbot = await self.get_chatbot_by_id(chatbot_id)

        if workspace_id is not None:
            chatbot.workspace_id = workspace_id
        if name is not None:
            chatbot.name = name
        if model_id is not None:
            chatbot.model_id = model_id
        if description is not None:
            chatbot.description = description
        if temperature is not None:
            chatbot.temperature = temperature
        if max_tokens is not None:
            chatbot.max_tokens = max_tokens
        if system_prompt is not None:
            chatbot.system_prompt = system_prompt
        if len(tools) > 0:
            chatbot.tools = tools
        if is_active is not None:
            if is_active:
                chatbot.activate()
            else:
                chatbot.deactivate()

        # Get existing model to preserve fields not in entity

        if hasattr(self.chatbot_repository, 'session'):
            result = await self.chatbot_repository.session.execute(
                select(ChatbotModel).where(ChatbotModel.id == chatbot_id)
            )
            existing_model = result.scalar_one_or_none()
            if existing_model:
                # Preserve fields from existing model if not provided
                final_model_id = model_id if model_id is not None else existing_model.model_id
                final_top_p = top_p if top_p is not None else existing_model.top_p
                final_welcome_message = welcome_message if welcome_message is not None else existing_model.welcome_message
                final_fallback_message = fallback_message if fallback_message is not None else existing_model.fallback_message
                final_max_conversation_length = max_conversation_length if max_conversation_length is not None else existing_model.max_conversation_length
                final_enable_function_calling = enable_function_calling if enable_function_calling is not None else existing_model.enable_function_calling
            else:
                # Use defaults if model not found
                from decimal import Decimal
                final_model_id = model_id
                final_top_p = top_p if top_p is not None else Decimal("1.0")
                final_welcome_message = welcome_message
                final_fallback_message = fallback_message
                final_max_conversation_length = max_conversation_length if max_conversation_length is not None else 50
                final_enable_function_calling = enable_function_calling if enable_function_calling is not None else True
        else:
            from decimal import Decimal
            final_model_id = model_id
            final_top_p = top_p if top_p is not None else Decimal("1.0")
            final_welcome_message = welcome_message
            final_fallback_message = fallback_message
            final_max_conversation_length = max_conversation_length if max_conversation_length is not None else 50
            final_enable_function_calling = enable_function_calling if enable_function_calling is not None else True
        
        # Use assigned_by as created_by for update
        created_by = assigned_by if assigned_by else chatbot.workspace_id
        
        updated_chatbot = await self.chatbot_repository.update(
            chatbot,
            created_by=created_by,
            model_id=final_model_id,
            top_p=final_top_p,
            welcome_message=final_welcome_message,
            fallback_message=final_fallback_message,
            max_conversation_length=final_max_conversation_length,
            enable_function_calling=final_enable_function_calling
        )

        # Update group assignments if provided
        if group_ids is not None:
            if not assigned_by:
                raise ValidationError("assigned_by is required when updating group assignments")

            # Validate group IDs
            if self.group_repository:
                for group_id in group_ids:
                    if not await self.group_repository.exists(group_id):
                        raise ValidationError(f"Group with ID {group_id} not found")

            if self.group_chatbot_repository:
                await self.group_chatbot_repository.assign_chatbot_to_groups(
                    chatbot_id=chatbot_id,
                    group_ids=group_ids,
                    assigned_by=assigned_by
                )

        # Update user assignments if provided
        if user_ids is not None:
            if not assigned_by:
                raise ValidationError("assigned_by is required when updating user assignments")

            # Validate user IDs
            if self.user_repository:
                for user_id in user_ids:
                    if not await self.user_repository.exists(user_id):
                        raise ValidationError(f"User with ID {user_id} not found")

            if self.user_chatbot_repository:
                await self.user_chatbot_repository.assign_chatbot_to_users(
                    chatbot_id=chatbot_id,
                    user_ids=user_ids,
                    assigned_by=assigned_by
                )

        return updated_chatbot

    async def delete_chatbot(self, chatbot_id: int) -> bool:
        """
        Delete chatbot.

        Args:
            chatbot_id: Chatbot ID (integer)

        Returns:
            bool: True if deleted

        Raises:
            NotFoundError: If chatbot not found
        """
        if not await self.chatbot_repository.exists(chatbot_id):
            raise NotFoundError(f"Chatbot with ID {chatbot_id} not found")

        return await self.chatbot_repository.delete(chatbot_id)
