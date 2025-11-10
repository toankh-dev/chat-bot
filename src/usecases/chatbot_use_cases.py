"""
Chatbot use cases.

Defines application-level use cases for chatbot operations.
"""

from typing import List, Optional
from application.services.chatbot_service import ChatbotService
from schemas.chatbot_schema import (
    ChatbotCreate,
    ChatbotUpdate,
    ChatbotResponse,
    UserInChatbot,
    GroupInChatbot,
    CreatorInfo
)
from domain.entities.user import UserEntity
from domain.entities.group import GroupEntity
from shared.utils.user_id_helper import extract_user_id_int
from shared.utils.security_helper import mask_api_key


def _convert_user_to_chatbot_user(user: UserEntity) -> UserInChatbot:
    """Convert UserEntity to UserInChatbot schema."""
    user_id_int = extract_user_id_int(user.id)
    return UserInChatbot(
        id=user_id_int,
        name=user.full_name,
        email=str(user.email)
    )


def _convert_group_to_chatbot_group(group: GroupEntity) -> GroupInChatbot:
    """Convert GroupEntity to GroupInChatbot schema."""
    return GroupInChatbot(
        id=group.id,
        name=group.name
    )


def _convert_user_to_creator_info(user: UserEntity) -> CreatorInfo:
    """Convert UserEntity to CreatorInfo schema."""
    user_id_int = extract_user_id_int(user.id)
    return CreatorInfo(
        id=user_id_int,
        name=user.full_name,
        email=str(user.email)
    )


def _convert_assignments(assigned_groups: Optional[List[GroupEntity]] = None,
                        assigned_users: Optional[List[UserEntity]] = None) -> tuple:
    """Convert assignment entities to schema objects."""
    groups = None
    if assigned_groups:
        groups = [_convert_group_to_chatbot_group(g) for g in assigned_groups]
    
    users = None
    if assigned_users:
        users = [_convert_user_to_chatbot_user(u) for u in assigned_users]
    
    return groups, users


class ListChatbotsUseCase:
    """
    Use case for listing chatbots.
    """

    def __init__(self, chatbot_service: ChatbotService):
        self.chatbot_service = chatbot_service

    async def execute(self, skip: int = 0, limit: int = 100) -> List[ChatbotResponse]:
        """
        Execute list chatbots use case.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[ChatbotResponse]: List of chatbots
        """
        chatbots = await self.chatbot_service.list_active_chatbots(skip=skip, limit=limit)
        responses = []
        for chatbot in chatbots:
            # Get model data for additional fields
            model_data = await self.chatbot_service.get_chatbot_model_data(chatbot.id)

            # Get creator info
            creator = None
            if model_data.get("created_by"):
                creator_user = await self.chatbot_service.get_chatbot_creator(model_data["created_by"])
                if creator_user:
                    creator = _convert_user_to_creator_info(creator_user)

            # Mask API key
            api_key_masked = None
            if model_data.get("api_key_encrypted"):
                # Remove "encrypted_" prefix if it exists
                raw_key = model_data["api_key_encrypted"]
                if raw_key.startswith("encrypted_"):
                    raw_key = raw_key.replace("encrypted_", "", 1)
                api_key_masked = mask_api_key(raw_key)

            chatbot_dict = {
                "id": chatbot.id,
                "name": chatbot.name,
                "description": chatbot.description or "",
                "provider": model_data["provider"],
                "model": model_data["model"],
                "temperature": chatbot.temperature,
                "max_tokens": chatbot.max_tokens,
                "top_p": model_data["top_p"],
                "system_prompt": chatbot.system_prompt or "",
                "welcome_message": model_data.get("welcome_message"),
                "fallback_message": model_data.get("fallback_message"),
                "max_conversation_length": model_data["max_conversation_length"],
                "enable_function_calling": model_data["enable_function_calling"],
                "api_key_masked": api_key_masked,
                "api_base_url": model_data.get("api_base_url"),
                "created_by": creator,
                "status": model_data["status"],
                "created_at": chatbot.created_at,
                "updated_at": chatbot.updated_at,
                "assigned_groups": None,  # Not loaded in list view
                "assigned_users": None
            }
            responses.append(ChatbotResponse.model_validate(chatbot_dict))
        return responses


class GetChatbotUseCase:
    """
    Use case for getting chatbot by ID.
    """

    def __init__(self, chatbot_service: ChatbotService):
        self.chatbot_service = chatbot_service

    async def execute(self, chatbot_id: int) -> ChatbotResponse:
        """
        Execute get chatbot use case.

        Args:
            chatbot_id: Chatbot ID (integer)

        Returns:
            ChatbotResponse: Chatbot data with assignments
        """
        chatbot = await self.chatbot_service.get_chatbot_by_id(chatbot_id, include_assignments=True)
        model_data = await self.chatbot_service.get_chatbot_model_data(chatbot.id)

        # Convert assignments to schema format
        assigned_groups = getattr(chatbot, 'assigned_groups', None)
        assigned_users = getattr(chatbot, 'assigned_users', None)
        groups, users = _convert_assignments(assigned_groups, assigned_users)

        # Get creator info
        creator = None
        if model_data.get("created_by"):
            creator_user = await self.chatbot_service.get_chatbot_creator(model_data["created_by"])
            if creator_user:
                creator = _convert_user_to_creator_info(creator_user)

        # Mask API key
        api_key_masked = None
        if model_data.get("api_key_encrypted"):
            # Remove "encrypted_" prefix if it exists
            raw_key = model_data["api_key_encrypted"]
            if raw_key.startswith("encrypted_"):
                raw_key = raw_key.replace("encrypted_", "", 1)
            api_key_masked = mask_api_key(raw_key)

        # Build response with assignments
        chatbot_dict = {
            "id": chatbot.id,
            "name": chatbot.name,
            "description": chatbot.description or "",
            "provider": model_data["provider"],
            "model": model_data["model"],
            "temperature": chatbot.temperature,
            "max_tokens": chatbot.max_tokens,
            "top_p": model_data["top_p"],
            "system_prompt": chatbot.system_prompt or "",
            "welcome_message": model_data.get("welcome_message"),
            "fallback_message": model_data.get("fallback_message"),
            "max_conversation_length": model_data["max_conversation_length"],
            "enable_function_calling": model_data["enable_function_calling"],
            "api_key_masked": api_key_masked,
            "api_base_url": model_data.get("api_base_url"),
            "created_by": creator,
            "status": model_data["status"],
            "created_at": chatbot.created_at,
            "updated_at": chatbot.updated_at,
            "assigned_groups": groups,
            "assigned_users": users
        }
        return ChatbotResponse.model_validate(chatbot_dict)


class CreateChatbotUseCase:
    """
    Use case for creating chatbot.
    """

    def __init__(self, chatbot_service: ChatbotService):
        self.chatbot_service = chatbot_service

    async def execute(self, request: ChatbotCreate, creator_id: int) -> ChatbotResponse:
        """
        Execute create chatbot use case.

        Args:
            request: Chatbot creation data
            creator_id: ID of user creating the chatbot

        Returns:
            ChatbotResponse: Created chatbot data with assignments
        """
        # For now, use simple "encryption" - in production, use proper encryption
        api_key_encrypted = f"encrypted_{request.api_key}"

        # Use creator_id as workspace_id (temporary until workspace model is ready)
        workspace_id = creator_id
        
        chatbot = await self.chatbot_service.create_chatbot(
            workspace_id=workspace_id,
            name=request.name,
            model_id=request.model,
            description=request.description,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            tools=[],  # Tools would be loaded separately
            group_ids=request.group_ids,
            user_ids=request.user_ids,
            assigned_by=creator_id,
            provider=request.provider,
            top_p=request.top_p,
            welcome_message=request.welcome_message,
            fallback_message=request.fallback_message,
            max_conversation_length=request.max_conversation_length,
            enable_function_calling=request.enable_function_calling,
            api_key_encrypted=api_key_encrypted,
            api_base_url=request.api_base_url
        )

        # Load chatbot with assignments for response
        chatbot = await self.chatbot_service.get_chatbot_by_id(chatbot.id, include_assignments=True)
        model_data = await self.chatbot_service.get_chatbot_model_data(chatbot.id)

        # Convert assignments to schema format
        assigned_groups = getattr(chatbot, 'assigned_groups', None)
        assigned_users = getattr(chatbot, 'assigned_users', None)
        groups, users = _convert_assignments(assigned_groups, assigned_users)

        # Get creator info
        creator = None
        if model_data.get("created_by"):
            creator_user = await self.chatbot_service.get_chatbot_creator(model_data["created_by"])
            if creator_user:
                creator = _convert_user_to_creator_info(creator_user)

        # Mask API key
        api_key_masked = None
        if model_data.get("api_key_encrypted"):
            raw_key = model_data["api_key_encrypted"]
            if raw_key.startswith("encrypted_"):
                raw_key = raw_key.replace("encrypted_", "", 1)
            api_key_masked = mask_api_key(raw_key)

        chatbot_dict = {
            "id": chatbot.id,
            "name": chatbot.name,
            "description": chatbot.description or "",
            "provider": model_data["provider"],
            "model": model_data["model"],
            "temperature": chatbot.temperature,
            "max_tokens": chatbot.max_tokens,
            "top_p": model_data["top_p"],
            "system_prompt": chatbot.system_prompt or "",
            "welcome_message": model_data.get("welcome_message"),
            "fallback_message": model_data.get("fallback_message"),
            "max_conversation_length": model_data["max_conversation_length"],
            "enable_function_calling": model_data["enable_function_calling"],
            "api_key_masked": api_key_masked,
            "api_base_url": model_data.get("api_base_url"),
            "created_by": creator,
            "status": model_data["status"],
            "created_at": chatbot.created_at,
            "updated_at": chatbot.updated_at,
            "assigned_groups": groups,
            "assigned_users": users
        }
        return ChatbotResponse.model_validate(chatbot_dict)


class UpdateChatbotUseCase:
    """
    Use case for updating chatbot.
    """

    def __init__(self, chatbot_service: ChatbotService):
        self.chatbot_service = chatbot_service

    async def execute(self, chatbot_id: int, request: ChatbotUpdate, admin_id: int) -> ChatbotResponse:
        """
        Execute update chatbot use case.

        Args:
            chatbot_id: Chatbot ID
            request: Chatbot update data
            admin_id: ID of admin updating the chatbot

        Returns:
            ChatbotResponse: Updated chatbot data with assignments
        """
        # Get existing chatbot to preserve workspace_id and model_id
        existing_chatbot = await self.chatbot_service.get_chatbot_by_id(chatbot_id)

        # Handle API key encryption if provided
        api_key_encrypted = None
        if request.api_key is not None:
            # Encrypt the new API key (use simple "encryption" for now, replace with proper encryption in production)
            api_key_encrypted = f"encrypted_{request.api_key}"

        chatbot = await self.chatbot_service.update_chatbot(
            chatbot_id=chatbot_id,
            workspace_id=existing_chatbot.workspace_id,
            name=request.name if request.name is not None else existing_chatbot.name,
            model_id=existing_chatbot.model_id,  # Model ID not updatable in this version
            description=request.description if request.description is not None else existing_chatbot.description,
            system_prompt=request.system_prompt if request.system_prompt is not None else existing_chatbot.system_prompt,
            temperature=request.temperature if request.temperature is not None else existing_chatbot.temperature,
            max_tokens=request.max_tokens if request.max_tokens is not None else existing_chatbot.max_tokens,
            tools=[],  # Tools not updatable in this version
            is_active=request.status == "active" if request.status is not None else existing_chatbot.is_active,
            group_ids=request.group_ids,
            user_ids=request.user_ids,
            assigned_by=admin_id,
            top_p=request.top_p if request.top_p is not None else None,
            welcome_message=request.welcome_message if request.welcome_message is not None else None,
            fallback_message=request.fallback_message if request.fallback_message is not None else None,
            max_conversation_length=request.max_conversation_length if request.max_conversation_length is not None else None,
            enable_function_calling=request.enable_function_calling if request.enable_function_calling is not None else None,
            api_key_encrypted=api_key_encrypted,
            api_base_url=request.api_base_url if request.api_base_url is not None else None
        )

        # Load chatbot with assignments for response
        chatbot = await self.chatbot_service.get_chatbot_by_id(chatbot_id, include_assignments=True)
        model_data = await self.chatbot_service.get_chatbot_model_data(chatbot.id)

        # Convert assignments to schema format
        assigned_groups = getattr(chatbot, 'assigned_groups', None)
        assigned_users = getattr(chatbot, 'assigned_users', None)
        groups, users = _convert_assignments(assigned_groups, assigned_users)

        # Get creator info
        creator = None
        if model_data.get("created_by"):
            creator_user = await self.chatbot_service.get_chatbot_creator(model_data["created_by"])
            if creator_user:
                creator = _convert_user_to_creator_info(creator_user)

        # Mask API key
        api_key_masked = None
        if model_data.get("api_key_encrypted"):
            raw_key = model_data["api_key_encrypted"]
            if raw_key.startswith("encrypted_"):
                raw_key = raw_key.replace("encrypted_", "", 1)
            api_key_masked = mask_api_key(raw_key)

        chatbot_dict = {
            "id": chatbot.id,
            "name": chatbot.name,
            "description": chatbot.description or "",
            "provider": model_data["provider"],
            "model": model_data["model"],
            "temperature": chatbot.temperature,
            "max_tokens": chatbot.max_tokens,
            "top_p": model_data["top_p"],
            "system_prompt": chatbot.system_prompt or "",
            "welcome_message": model_data.get("welcome_message"),
            "fallback_message": model_data.get("fallback_message"),
            "max_conversation_length": model_data["max_conversation_length"],
            "enable_function_calling": model_data["enable_function_calling"],
            "api_key_masked": api_key_masked,
            "api_base_url": model_data.get("api_base_url"),
            "created_by": creator,
            "status": model_data["status"],
            "created_at": chatbot.created_at,
            "updated_at": chatbot.updated_at,
            "assigned_groups": groups,
            "assigned_users": users
        }
        return ChatbotResponse.model_validate(chatbot_dict)


class DeleteChatbotUseCase:
    """
    Use case for deleting chatbot.
    """

    def __init__(self, chatbot_service: ChatbotService):
        self.chatbot_service = chatbot_service

    async def execute(self, chatbot_id: int) -> bool:
        """
        Execute delete chatbot use case.

        Args:
            chatbot_id: Chatbot ID

        Returns:
            bool: True if deleted
        """
        return await self.chatbot_service.delete_chatbot(chatbot_id)
