"""Encryption Service Interface."""

from abc import ABC, abstractmethod
from typing import Optional


class IEncryptionService(ABC):
    """Interface for encryption service operations."""

    @abstractmethod
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Encrypted string (base64 encoded)
        """
        pass

    @abstractmethod
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext string.

        Args:
            ciphertext: Encrypted string (base64 encoded)

        Returns:
            Decrypted plaintext string
        """
        pass
