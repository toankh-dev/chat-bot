"""
Unit tests for domain entities.
"""

import pytest
from datetime import datetime
from src.domain.entities.user import UserEntity
from src.domain.entities.role import RoleEntity
from src.domain.entities.workspace import WorkspaceEntity
from src.domain.entities.chatbot import ChatbotEntity
from src.domain.entities.message import MessageEntity, MessageRole, MessageStatus
from src.domain.value_objects.email import Email
from src.domain.value_objects.uuid_vo import UUID


class TestUser:
    """Tests for User entity."""

    def test_create_user(self):
        """Test creating a valid user."""
        user = UserEntity(
            id=UUID.generate(),
            email=Email("test@example.com"),
            username="testuser",
            full_name="Test User",
            hashed_password="hashed_password_here"
        )

        assert user.username == "testuser"
        assert str(user.email) == "test@example.com"
        assert user.is_active is True
        assert user.is_superuser is False

    def test_user_invalid_username(self):
        """Test user creation with invalid username."""
        with pytest.raises(ValueError):
            UserEntity(
                id=UUID.generate(),
                email=Email("test@example.com"),
                username="ab",  # Too short
                full_name="Test User",
                hashed_password="hashed"
            )

    def test_user_deactivate(self):
        """Test deactivating a user."""
        user = UserEntity(
            id=UUID.generate(),
            email=Email("test@example.com"),
            username="testuser",
            full_name="Test User",
            hashed_password="hashed"
        )

        user.deactivate()
        assert user.is_active is False

    def test_user_record_login(self):
        """Test recording user login."""
        user = UserEntity(
            id=UUID.generate(),
            email=Email("test@example.com"),
            username="testuser",
            full_name="Test User",
            hashed_password="hashed"
        )

        assert user.last_login_at is None
        user.record_login()
        assert user.last_login_at is not None


class TestRole:
    """Tests for Role entity."""

    def test_create_role(self):
        """Test creating a valid role."""
        role = RoleEntity(
            id=UUID.generate(),
            name="admin",
            description="Administrator role",
            permissions={RoleEntity.PERM_ADMIN}
        )

        assert role.name == "admin"
        assert RoleEntity.PERM_ADMIN in role.permissions

    def test_add_permission(self):
        """Test adding permission to role."""
        role = RoleEntity(
            id=UUID.generate(),
            name="user",
            description="Regular user"
        )

        role.add_permission(RoleEntity.PERM_USER_READ)
        assert RoleEntity.PERM_USER_READ in role.permissions

    def test_has_permission(self):
        """Test checking if role has permission."""
        role = Role(
            id=UUID.generate(),
            name="user",
            description="Regular user",
            permissions={Role.PERM_USER_READ}
        )

        assert role.has_permission(Role.PERM_USER_READ) is True
        assert role.has_permission(Role.PERM_USER_WRITE) is False


class TestMessage:
    """Tests for Message entity."""

    def test_create_message(self):
        """Test creating a valid message."""
        message = MessageEntity(
            id=UUID.generate(),
            conversation_id=UUID.generate(),
            session_id=UUID.generate(),
            role=MessageRole.USER,
            content="Hello, AI!"
        )

        assert message.role == MessageRole.USER
        assert message.content == "Hello, AI!"
        assert message.status == MessageStatus.PENDING

    def test_mark_as_completed(self):
        """Test marking message as completed."""
        message = MessageEntity(
            id=UUID.generate(),
            conversation_id=UUID.generate(),
            session_id=UUID.generate(),
            role=MessageRole.ASSISTANT,
            content="Hello!"
        )

        message.mark_as_completed(tokens_used=50)
        assert message.status == MessageStatus.COMPLETED
        assert message.tokens_used == 50


class TestChatbot:
    """Tests for Chatbot entity."""

    def test_create_chatbot(self):
        """Test creating a valid chatbot."""
        chatbot = MessageEntity(
            id=UUID.generate(),
            workspace_id=UUID.generate(),
            name="Test Bot",
            description="A test chatbot",
            system_prompt="You are a helpful assistant"
        )

        assert chatbot.name == "Test Bot"
        assert chatbot.temperature == 0.7
        assert chatbot.is_active is True

    def test_invalid_temperature(self):
        """Test chatbot with invalid temperature."""
        with pytest.raises(ValueError):
            MessageEntity(
                id=UUID.generate(),
                workspace_id=UUID.generate(),
                name="Test Bot",
                description="Test",
                system_prompt="Test",
                temperature=1.5  # Invalid
            )

    def test_add_tool(self):
        """Test adding a tool to chatbot."""
        chatbot = MessageEntity(
            id=UUID.generate(),
            workspace_id=UUID.generate(),
            name="Test Bot",
            description="Test",
            system_prompt="Test"
        )

        chatbot.add_tool("web_search")
        assert "web_search" in chatbot.tools
