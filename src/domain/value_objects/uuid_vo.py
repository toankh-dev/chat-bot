"""
UUID value object for type-safe entity identification.
"""

import uuid
from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class UUID:
    """
    Value object representing a UUID identifier.

    Provides type safety and validation for entity IDs.
    """

    value: str

    def __post_init__(self):
        """Validate UUID format."""
        try:
            if isinstance(self.value, uuid.UUID):
                # Re-assign value to its string representation using object.__setattr__
                object.__setattr__(self, "value", str(self.value))
            else:
                uuid.UUID(self.value)
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid UUID format: {self.value}")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> 'UUID':
        """Generate a new random UUID."""
        return cls(value=str(uuid.uuid4()))

    @classmethod
    def from_string(cls, value: Union[str, 'UUID']) -> 'UUID':
        """Create UUID from string or return existing UUID."""
        if isinstance(value, UUID):
            return value
        return cls(value=value)
