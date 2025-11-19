from typing import Optional, Tuple

from fastapi import Request


def get_request_creds(request: Request) -> Tuple[Optional[str], Optional[str]]:
    """
    Return (username, password) from request.state if set by auth middleware.
    Returns (None, None) if not set.
    """
    return getattr(request.state, "username", None), getattr(
        request.state, "password", None
    )
