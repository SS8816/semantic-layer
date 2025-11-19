"""
Authentication API endpoints
"""

from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.services.auth_service import auth_service
from app.services.token_manager import token_manager
from app.utils.logger import app_logger as logger

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    """Login request model"""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model"""

    success: bool
    message: str
    token: str
    user: Optional[dict] = None


class UserResponse(BaseModel):
    """Current user response model"""

    username: str
    display_name: str
    email: str
    groups: list
    roles: list


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login endpoint - authenticates user and creates bearer token

    Args:
        request: Login credentials

    Returns:
        LoginResponse with bearer token and user info
    """
    try:
        logger.info(f"Login attempt for user: {request.username}")

        # Authenticate with HERE's endpoint
        user_info = auth_service.authenticate_user(request.username, request.password)

        if not user_info:
            logger.warning(f"Login failed for user: {request.username}")
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Create bearer token
        token = token_manager.create_token(
            username=request.username, password=request.password, user_info=user_info
        )

        logger.info(f"Login successful for user: {request.username}")

        return LoginResponse(
            success=True, message="Login successful", token=token, user=user_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for user {request.username}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me", response_model=UserResponse)
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Get current authenticated user

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        Current user information
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Extract token from "Bearer <token>"
    token = authorization.replace("Bearer ", "")

    # Validate token
    token_data = token_manager.validate_token(token)

    if not token_data:
        raise HTTPException(status_code=401, detail="Token expired or invalid")

    user_info = token_data.get("user_info", {})

    return UserResponse(
        username=user_info.get("username", ""),
        display_name=user_info.get("display_name", ""),
        email=user_info.get("email", ""),
        groups=user_info.get("groups", []),
        roles=user_info.get("roles", []),
    )


@router.post("/logout")
async def logout():
    """
    Logout endpoint - with token-based auth, client handles token removal

    Returns:
        Success message
    """
    logger.info("User logged out")
    return {"success": True, "message": "Logged out successfully"}


@router.get("/token-info")
async def get_token_info(authorization: Optional[str] = Header(None)):
    """
    Get token information (for debugging)

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        Token info
    """
    if not authorization or not authorization.startswith("Bearer "):
        return {"authenticated": False}

    # Extract token from "Bearer <token>"
    token = authorization.replace("Bearer ", "")

    # Validate token
    token_data = token_manager.validate_token(token)

    if not token_data:
        return {"authenticated": False}

    return {
        "authenticated": True,
        "username": token_data.get("username"),
        "created_at": token_data.get("created_at"),
        "expires_at": token_data.get("expires_at"),
    }
