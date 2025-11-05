"""
Unit tests for value objects.
"""

import pytest
from src.domain.value_objects.email import Email
from src.domain.value_objects.uuid_vo import UUID
import uuid as std_uuid


class TestEmail:
    """Tests for Email value object."""

    def test_valid_email(self):
        """Test creating valid email."""
        email = Email("test@example.com")
        assert str(email) == "test@example.com"
        assert email.domain == "example.com"
        assert email.local_part == "test"

    def test_invalid_email_format(self):
        """Test invalid email format."""
        with pytest.raises(ValueError):
            Email("invalid-email")

        with pytest.raises(ValueError):
            Email("@example.com")

        with pytest.raises(ValueError):
            Email("test@")

    def test_email_immutability(self):
        """Test that email is immutable."""
        email = Email("test@example.com")
        with pytest.raises(AttributeError):
            email.value = "other@example.com"


class TestUUID:
    """Tests for UUID value object."""

    def test_generate_uuid(self):
        """Test generating new UUID."""
        uuid1 = UUID.generate()
        uuid2 = UUID.generate()

        assert uuid1 != uuid2
        assert isinstance(str(uuid1), str)

    def test_create_from_string(self):
        """Test creating UUID from string."""
        uuid_str = str(std_uuid.uuid4())
        uuid_obj = UUID(value=uuid_str)

        assert str(uuid_obj) == uuid_str

    def test_invalid_uuid(self):
        """Test invalid UUID format."""
        with pytest.raises(ValueError):
            UUID("invalid-uuid")

    def test_from_string_with_uuid_object(self):
        """Test from_string with existing UUID object."""
        uuid1 = UUID.generate()
        uuid2 = UUID.from_string(uuid1)

        assert uuid1 == uuid2
