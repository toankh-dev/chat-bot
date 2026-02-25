"""
Token encryption service for secure credential storage.
"""

import base64
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from core.config import settings


class TokenEncryptionService:
    """Service for encrypting/decrypting sensitive tokens."""

    def __init__(self):
        """Initialize encryption service with key from settings."""
        # Get encryption key from environment
        encryption_key = os.getenv('TOKEN_ENCRYPTION_KEY')

        if not encryption_key:
            # Development fallback - generate from secret key
            # PRODUCTION: Must set TOKEN_ENCRYPTION_KEY env var
            if settings.ENVIRONMENT == 'production':
                raise ValueError("TOKEN_ENCRYPTION_KEY must be set in production")

            # Derive key from JWT_SECRET_KEY for development
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'kass_dev_salt',  # Fixed salt for dev only
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(
                kdf.derive(settings.JWT_SECRET_KEY.encode())
            )
            encryption_key = key.decode()

        self.fernet = Fernet(encryption_key.encode())

    def encrypt_token(self, token: str) -> str:
        """
        Encrypt a token for storage.

        Args:
            token: Plain text token

        Returns:
            Encrypted token as base64 string
        """
        if not token:
            return ""

        encrypted = self.fernet.encrypt(token.encode())
        return encrypted.decode()

    def decrypt_token(self, encrypted_token: str) -> Optional[str]:
        """
        Decrypt a stored token.

        Args:
            encrypted_token: Encrypted token string

        Returns:
            Plain text token or None if decryption fails
        """
        if not encrypted_token:
            return None

        try:
            decrypted = self.fernet.decrypt(encrypted_token.encode())
            return decrypted.decode()
        except Exception as e:
            # Log error but don't expose details
            print(f"Token decryption failed: {type(e).__name__}")
            return None

    def rotate_token(self, old_encrypted_token: str, new_token: str) -> str:
        """
        Rotate a token (decrypt old, encrypt new).

        Args:
            old_encrypted_token: Currently stored encrypted token
            new_token: New plain text token

        Returns:
            New encrypted token
        """
        # Verify old token can be decrypted
        old_token = self.decrypt_token(old_encrypted_token)
        if old_token is None:
            raise ValueError("Failed to decrypt old token")

        # Encrypt new token
        return self.encrypt_token(new_token)


# Singleton instance
_encryption_service: Optional[TokenEncryptionService] = None


def get_token_encryption_service() -> TokenEncryptionService:
    """Get singleton instance of token encryption service."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = TokenEncryptionService()
    return _encryption_service
