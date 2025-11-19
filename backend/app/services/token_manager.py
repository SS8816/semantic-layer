"""
Token Manager
Handles bearer token generation and validation
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Optional

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings
from app.utils.logger import app_logger as logger


class TokenManager:
    """Manages bearer tokens for authentication"""

    def __init__(self, token_duration_days: int = 3):
        """
        Initialize token manager

        Args:
            token_duration_days: Number of days before token expires
        """
        self.token_duration = timedelta(days=token_duration_days)

        secret_key = settings.session_secret_key

        if isinstance(secret_key, str):
            secret_key = secret_key.encode()

        self.cipher = Fernet(secret_key)

    def _encrypt_password(self, password: str) -> str:
        """
        Encrypt password using Fernet symmetric encryption

        Args:
            password: Plain text password

        Returns:
            Encrypted password (as string)
        """
        encrypted_bytes = self.cipher.encrypt(password.encode())
        return encrypted_bytes.decode()

    def _decrypt_password(self, encrypted: str) -> str:
        """
        Decrypt password

        Args:
            encrypted: Encrypted password string

        Returns:
            Plain text password
        """
        decrypted_bytes = self.cipher.decrypt(encrypted.encode())
        return decrypted_bytes.decode()

    def create_token(self, username: str, password: str, user_info: Dict) -> str:
        """
        Create a new bearer token

        Args:
            username: User's username
            password: User's password (will be encrypted)
            user_info: Additional user information

        Returns:
            Bearer token (encrypted, self-contained)
        """
        # Calculate expiration
        expires_at = datetime.utcnow() + self.token_duration

        # Encrypt password before storing in token
        encrypted_password = self._encrypt_password(password)

        # Create token payload
        payload = {
            "username": username,
            "password": encrypted_password,  # Encrypted!
            "user_info": user_info,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        # Encrypt entire payload
        payload_json = json.dumps(payload)
        token_bytes = self.cipher.encrypt(payload_json.encode())
        token = token_bytes.decode()

        logger.info(f"Created token for user {username}, expires at {expires_at}")
        return token

    def validate_token(self, token: str) -> Optional[Dict]:
        """
        Validate and decode bearer token

        Args:
            token: Bearer token string

        Returns:
            Token data with decrypted password if valid, None otherwise
        """
        try:
            # Decrypt token
            token_bytes = self.cipher.decrypt(token.encode())
            payload_json = token_bytes.decode()
            payload = json.loads(payload_json)

            # Check if expired
            expires_at = datetime.fromisoformat(payload["expires_at"])
            if datetime.utcnow() > expires_at:
                logger.info(f"Token expired for user {payload.get('username')}")
                return None

            # Decrypt password before returning
            payload["password"] = self._decrypt_password(payload["password"])

            return payload

        except (InvalidToken, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Invalid token: {e}")
            return None


# Global instance
token_manager = TokenManager(token_duration_days=3)
