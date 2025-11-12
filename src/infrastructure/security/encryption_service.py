"""
Encryption Service for securing sensitive connector credentials.
"""

import base64
import os
from typing import Optional
from cryptography.fernet import Fernet
from core.config import settings
from core.logger import logger


class EncryptionService:
    """
    Service for encrypting/decrypting sensitive data like OAuth credentials.
    
    Uses Fernet symmetric encryption for secure storage of:
    - OAuth client secrets
    - API tokens
    - Other sensitive connector data
    """

    def __init__(self):
        """Initialize encryption service with key from environment."""
        self._key = self._get_encryption_key()
        self._cipher = Fernet(self._key)
        logger.info("EncryptionService initialized successfully")

    def _get_encryption_key(self) -> bytes:
        """
        Get encryption key from environment or generate new one.
        
        Returns:
            Encryption key as bytes
            
        Raises:
            ValueError: If key cannot be loaded or generated
        """
        try:
            # Try to get key from environment
            key_env = getattr(settings, 'ENCRYPTION_KEY', None) or os.getenv("ENCRYPTION_KEY")
            
            if key_env:
                try:
                    # Decode base64 encoded key
                    key = base64.urlsafe_b64decode(key_env.encode())
                    # Validate key by creating cipher
                    Fernet(key)
                    logger.info("Loaded encryption key from environment")
                    return key
                except Exception as e:
                    logger.error(f"Invalid encryption key in environment: {e}")
                    raise ValueError(f"Invalid encryption key format: {e}")
            
            # Generate new key for development (NOT for production!)
            if getattr(settings, 'ENVIRONMENT', 'development') == 'development':
                logger.warning("No encryption key found - generating new key for development")
                key = Fernet.generate_key()
                key_b64 = base64.urlsafe_b64encode(key).decode()
                logger.warning(f"Generated encryption key: {key_b64}")
                logger.warning("⚠️  Store this key in ENCRYPTION_KEY environment variable!")
                return key
            
            # In production, require explicit key
            raise ValueError(
                "ENCRYPTION_KEY environment variable is required in production. "
                "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption key: {e}")
            raise

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string value.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64 encoded encrypted string
            
        Raises:
            ValueError: If encryption fails
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")
            
        try:
            encrypted_bytes = self._cipher.encrypt(plaintext.encode('utf-8'))
            encrypted_b64 = base64.urlsafe_b64encode(encrypted_bytes).decode('ascii')
            logger.debug("Successfully encrypted data")
            return encrypted_b64
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Failed to encrypt data: {e}")

    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt an encrypted string value.
        
        Args:
            encrypted_text: Base64 encoded encrypted string
            
        Returns:
            Decrypted plaintext string
            
        Raises:
            ValueError: If decryption fails
        """
        if not encrypted_text:
            raise ValueError("Cannot decrypt empty string")
            
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode('ascii'))
            decrypted_bytes = self._cipher.decrypt(encrypted_bytes)
            plaintext = decrypted_bytes.decode('utf-8')
            logger.debug("Successfully decrypted data")
            return plaintext
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Failed to decrypt data: {e}")

    def encrypt_if_not_empty(self, plaintext: Optional[str]) -> Optional[str]:
        """
        Encrypt string only if it's not empty.
        
        Args:
            plaintext: String to encrypt (can be None or empty)
            
        Returns:
            Encrypted string or None
        """
        if plaintext and plaintext.strip():
            return self.encrypt(plaintext.strip())
        return None

    def decrypt_if_not_empty(self, encrypted_text: Optional[str]) -> Optional[str]:
        """
        Decrypt string only if it's not empty.
        
        Args:
            encrypted_text: Encrypted string (can be None or empty)
            
        Returns:
            Decrypted string or None
        """
        if encrypted_text and encrypted_text.strip():
            return self.decrypt(encrypted_text.strip())
        return None

    def is_encrypted(self, text: str) -> bool:
        """
        Check if a string appears to be encrypted.
        
        Args:
            text: String to check
            
        Returns:
            True if string appears encrypted, False otherwise
        """
        if not text:
            return False
            
        try:
            # Try to decode as base64 and decrypt
            base64.urlsafe_b64decode(text.encode('ascii'))
            return True
        except Exception:
            return False

    def rotate_encryption(self, old_encrypted: str, old_key: str) -> str:
        """
        Rotate encryption with new key.
        
        Args:
            old_encrypted: Data encrypted with old key
            old_key: Old encryption key (base64 encoded)
            
        Returns:
            Data re-encrypted with current key
        """
        try:
            # Create cipher with old key
            old_key_bytes = base64.urlsafe_b64decode(old_key.encode())
            old_cipher = Fernet(old_key_bytes)
            
            # Decrypt with old key
            encrypted_bytes = base64.urlsafe_b64decode(old_encrypted.encode('ascii'))
            plaintext_bytes = old_cipher.decrypt(encrypted_bytes)
            plaintext = plaintext_bytes.decode('utf-8')
            
            # Re-encrypt with current key
            return self.encrypt(plaintext)
            
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            raise ValueError(f"Failed to rotate encryption: {e}")

    def validate_key_format(self, key_b64: str) -> bool:
        """
        Validate encryption key format.
        
        Args:
            key_b64: Base64 encoded key to validate
            
        Returns:
            True if key is valid, False otherwise
        """
        try:
            key_bytes = base64.urlsafe_b64decode(key_b64.encode())
            Fernet(key_bytes)
            return True
        except Exception:
            return False

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key.
        
        Returns:
            Base64 encoded encryption key
        """
        key = Fernet.generate_key()
        return base64.urlsafe_b64encode(key).decode()

    def __del__(self):
        """Clean up encryption resources."""
        # Clear sensitive data from memory
        if hasattr(self, '_key'):
            del self._key
        if hasattr(self, '_cipher'):
            del self._cipher