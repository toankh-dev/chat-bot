"""
Email value object with validation.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """
    Value object representing a validated email address.

    Attributes:
        value: The email address string
    """

    value: str

    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    def __post_init__(self):
        """Validate email format."""
        if not self.EMAIL_REGEX.match(self.value):
            raise ValueError(f"Invalid email format: {self.value}")

    def __str__(self) -> str:
        return self.value

    @property
    def domain(self) -> str:
        """Extract domain from email."""
        return self.value.split('@')[1]

    @property
    def local_part(self) -> str:
        """Extract local part from email."""
        return self.value.split('@')[0]
