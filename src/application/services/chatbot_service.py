"""
ChatbotEntity service.

Handles chatbot management business logic.
"""

from typing import List, Optional
from decimal import Decimal
from core.errors import NotFoundError, ValidationError
from domain.value_objects.uuid_vo import UUID
from domain.entities.user import User
from domain.entities.chatbot import Chatbot
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

    async def get_chatbot_assigned_users(self, chatbot_id: int) -> List[User]:
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

    async def get_chatbot_by_id(self, chatbot_id: int, include_assignments: bool = False) -> Chatbot:
        """
        Get chatbot by ID.

        Args:
            chatbot_id: Chatbot ID
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

    async def list_chatbots(self, skip: int = 0, limit: int = 100) -> List[Chatbot]:
        """
        List all chatbots with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Chatbot]: List of chatbots
        """
        return await self.chatbot_repository.find_all(skip=skip, limit=limit)

    async def list_active_chatbots(self, skip: int = 0, limit: int = 100) -> List[Chatbot]:
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
        workspace_id: str,
        name: str,
        model_id: str,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Decimal = Decimal("0.7"),
        max_tokens: int = 2048,
        tools: List[str] = [],
        group_ids: Optional[List[int]] = None,
        user_ids: Optional[List[int]] = None,
        assigned_by: Optional[int] = None
    ) -> Chatbot:
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
            api_base_url: Custom API endpoint
            group_ids: Optional list of group IDs to assign chatbot to
            user_ids: Optional list of user IDs to assign chatbot to
            assigned_by: Admin ID who is making the assignments

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

        chatbot = Chatbot(
            id=UUID.generate(),
            workspace_id=workspace_id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            is_active=True,
        )

        created_chatbot = await self.chatbot_repository.create(chatbot)

        # Assign to groups if provided
        if group_ids and self.group_chatbot_repository:
            await self.group_chatbot_repository.assign_chatbot_to_groups(
                chatbot_id=created_chatbot.id,
                group_ids=group_ids,
                assigned_by=assigned_by  # type: ignore
            )

        # Assign to users if provided
        if user_ids and self.user_chatbot_repository:
            await self.user_chatbot_repository.assign_chatbot_to_users(
                chatbot_id=created_chatbot.id,
                user_ids=user_ids,
                assigned_by=assigned_by  # type: ignore
            )

        return created_chatbot

    async def update_chatbot(
        self,
        chatbot_id: str,
        workspace_id: str,
        name: str,
        model_id: str,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Decimal = Decimal("0.7"),
        max_tokens: int = 2048,
        tools: List[str] = [],
        is_active: Optional[bool] = None,
        group_ids: Optional[List[int]] = None,
        user_ids: Optional[List[int]] = None,
        assigned_by: Optional[int] = None
    ) -> Chatbot:
        """
        Update chatbot configuration.

        Args:
            chatbot_id: Chatbot ID
            name: New name (optional)
            description: New description (optional)
            temperature: New temperature (optional)
            max_tokens: New max tokens (optional)
            system_prompt: New system prompt (optional)
            is_active: Active status (optional)
            welcome_message: New welcome message (optional)
            fallback_message: New fallback message (optional)
            max_conversation_length: New context window (optional)
            enable_function_calling: Enable/disable tools (optional)
            status: New status (optional)
            group_ids: New list of group IDs (replaces existing, optional)
            user_ids: New list of user IDs (replaces existing, optional)
            assigned_by: Admin ID who is making the assignments

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

        updated_chatbot = await self.chatbot_repository.update(chatbot)

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

    async def delete_chatbot(self, chatbot_id: str) -> bool:
        """
        Delete chatbot.

        Args:
            chatbot_id: Chatbot ID

        Returns:
            bool: True if deleted

        Raises:
            NotFoundError: If chatbot not found
        """
        if not await self.chatbot_repository.exists(chatbot_id):
            raise NotFoundError(f"Chatbot with ID {chatbot_id} not found")

        return await self.chatbot_repository.delete(chatbot_id)
