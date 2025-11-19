"""
Session Manager
Handles user session storage and management
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

from cryptography.fernet import Fernet

from app.config import settings
from app.utils.logger import app_logger as logger


class SessionManager:
    """Manages user sessions in-memory"""

    def __init__(self, session_duration_days: int = 3):
        """
        Initialize session manager

        Args:
            session_duration_days: Number of days before session expires
        """
        self.sessions: Dict[str, Dict] = {}
        self.session_duration = timedelta(days=session_duration_days)

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

    def create_session(self, username: str, password: str, user_info: Dict) -> str:
        """
        Create a new session

        Args:
            username: User's username
            password: User's password (will be encrypted)
            user_info: Additional user information

        Returns:
            Session ID
        """
        # Generate unique session ID
        session_id = secrets.token_urlsafe(32)

        # Calculate expiration
        expires_at = datetime.utcnow() + self.session_duration

        # Encrypt password before storing
        encrypted_password = self._encrypt_password(password)

        # Store session
        self.sessions[session_id] = {
            "username": username,
            "password": encrypted_password,  # Encrypted!
            "user_info": user_info,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
        }

        logger.info(f"Created session for user {username}, expires at {expires_at}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session data with decrypted password

        Args:
            session_id: Session identifier

        Returns:
            Session data if valid, None otherwise
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id].copy()

        # Check if expired
        if datetime.utcnow() > session["expires_at"]:
            logger.info(f"Session {session_id} expired")
            self.delete_session(session_id)
            return None

        # Decrypt password before returning
        session["password"] = self._decrypt_password(session["password"])

        return session

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        if session_id in self.sessions:
            username = self.sessions[session_id].get("username")
            del self.sessions[session_id]
            logger.info(f"Deleted session for user {username}")
            return True
        return False

    def cleanup_expired_sessions(self):
        """Remove all expired sessions"""
        now = datetime.utcnow()
        expired = [
            sid for sid, session in self.sessions.items() if now > session["expires_at"]
        ]

        for sid in expired:
            self.delete_session(sid)

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

    def get_session_count(self) -> int:
        """Get total number of active sessions"""
        return len(self.sessions)


# Global instance
session_manager = SessionManager(session_duration_days=3)
