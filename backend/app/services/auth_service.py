"""
Authentication Service
Handles user authentication against HERE's authentication endpoint
"""

import base64
from typing import Dict, Optional

import requests

from app.utils.logger import app_logger as logger


class AuthService:
    """Service for authenticating users"""

    # HERE's authentication endpoint
    AUTH_ENDPOINT = (
        "https://visualization-api.analytics.in.here.com/api/v1/authenticate"
    )

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate user against HERE's auth endpoint

        Args:
            username: User's username
            password: User's password

        Returns:
            Dict with user info if successful, None if failed
        """
        try:
            # Create Basic Auth header
            credentials = f"{username}:{password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()

            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Accept": "application/json",
            }

            logger.info(f"Authenticating user: {username}")

            # Make request to HERE's auth endpoint
            response = requests.get(self.AUTH_ENDPOINT, headers=headers, timeout=10)

            if response.status_code == 200:
                user_info = response.json()
                logger.info(f"Successfully authenticated user: {username}")
                return {
                    "username": user_info.get("username"),
                    "display_name": user_info.get("user-display-name"),
                    "email": user_info.get("email"),
                    "groups": user_info.get("groups", []),
                    "roles": user_info.get("roles", []),
                }
            else:
                logger.warning(
                    f"Authentication failed for user {username}: {response.status_code}"
                )
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication request failed for user {username}: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error during authentication for user {username}: {e}"
            )
            return None

    def validate_credentials(self, username: str, password: str) -> bool:
        """
        Validate if credentials are correct

        Args:
            username: User's username
            password: User's password

        Returns:
            True if valid, False otherwise
        """
        user_info = self.authenticate_user(username, password)
        return user_info is not None


# Global instance
auth_service = AuthService()
