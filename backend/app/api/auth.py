"""
Authentication API endpoints
"""

from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel

from app.services.auth_service import auth_service
from app.services.session_manager import session_manager
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
    user: Optional[dict] = None


class UserResponse(BaseModel):
    """Current user response model"""

    username: str
    display_name: str
    email: str
    groups: list
    roles: list


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response):
    """
    Login endpoint - authenticates user and creates session

    Args:
        request: Login credentials
        response: FastAPI response object (for setting cookies)

    Returns:
        LoginResponse with user info
    """
    try:
        logger.info(f"Login attempt for user: {request.username}")

        # Authenticate with HERE's endpoint
        user_info = auth_service.authenticate_user(request.username, request.password)

        if not user_info:
            logger.warning(f"Login failed for user: {request.username}")
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Create session
        session_id = session_manager.create_session(
            username=request.username, password=request.password, user_info=user_info
        )

        # Set HTTP-only cookie
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,  # Cannot be accessed by JavaScript (XSS protection)
            secure=False,  # Only sent over HTTPS
            samesite="lax",  # CSRF protection
            max_age=60 * 60 * 24 * 3,  # 3 days in seconds
        )

        logger.info(f"Login successful for user: {request.username}")

        return LoginResponse(success=True, message="Login successful", user=user_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for user {request.username}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me", response_model=UserResponse)
async def get_current_user(session_id: Optional[str] = Cookie(None)):
    """
    Get current authenticated user

    Args:
        session_id: Session ID from cookie

    Returns:
        Current user information
    """
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = session_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    user_info = session.get("user_info", {})

    return UserResponse(
        username=user_info.get("username", ""),
        display_name=user_info.get("display_name", ""),
        email=user_info.get("email", ""),
        groups=user_info.get("groups", []),
        roles=user_info.get("roles", []),
    )


@router.post("/logout")
async def logout(response: Response, session_id: Optional[str] = Cookie(None)):
    """
    Logout endpoint - deletes session and clears cookie

    Args:
        response: FastAPI response object
        session_id: Session ID from cookie

    Returns:
        Success message
    """
    if session_id:
        session_manager.delete_session(session_id)
        logger.info("User logged out")

    # Clear cookie
    response.delete_cookie(key="session_id")

    return {"success": True, "message": "Logged out successfully"}


@router.get("/session-info")
async def get_session_info(session_id: Optional[str] = Cookie(None)):
    """
    Get session information (for debugging)

    Args:
        session_id: Session ID from cookie

    Returns:
        Session info
    """
    if not session_id:
        return {
            "authenticated": False,
            "total_sessions": session_manager.get_session_count(),
        }

    session = session_manager.get_session(session_id)

    if not session:
        return {
            "authenticated": False,
            "total_sessions": session_manager.get_session_count(),
        }

    return {
        "authenticated": True,
        "username": session.get("username"),
        "created_at": session.get("created_at").isoformat(),
        "expires_at": session.get("expires_at").isoformat(),
        "total_sessions": session_manager.get_session_count(),
    }
