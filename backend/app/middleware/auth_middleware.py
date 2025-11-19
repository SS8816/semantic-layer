"""
Authentication Middleware
Validates sessions and injects user credentials into requests
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.session_manager import session_manager
from app.utils.logger import app_logger as logger


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to validate authentication on protected routes"""

    # Routes that don't require authentication
    PUBLIC_ROUTES = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/auth/login",
        "/api/auth/logout",
    ]

    async def dispatch(self, request: Request, call_next):
        """
        Process each request

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response
        """
        path = request.url.path

        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip authentication for public routes
        if self._is_public_route(path):
            return await call_next(request)

        # Get session cookie
        session_id = request.cookies.get("session_id")

        if not session_id:
            logger.warning(f"Unauthenticated request to protected route: {path}")
            return JSONResponse(
                status_code=401, content={"detail": "Not authenticated. Please log in."}
            )

        # Validate session
        session = session_manager.get_session(session_id)

        if not session:
            logger.warning(f"Invalid or expired session for route: {path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Session expired. Please log in again."},
            )

        # Inject user credentials into request state
        request.state.username = session.get("username")
        request.state.password = session.get("password")
        request.state.user_info = session.get("user_info")

        # Continue to route handler
        response = await call_next(request)
        return response

    def _is_public_route(self, path: str) -> bool:
        """
        Check if route is public (doesn't require auth)

        Args:
            path: Request path

        Returns:
            True if public, False if protected
        """
        # Exact match
        if path in self.PUBLIC_ROUTES:
            return True

        # Prefix match for static files, docs, etc.
        public_prefixes = ["/docs", "/redoc", "/openapi.json", "/api/relationships"]
        for prefix in public_prefixes:
            if path.startswith(prefix):
                return True

        return False
