"""
Simple dependency functions for FastAPI routes.

Provides easy-to-use dependencies for authentication and authorization.
"""

from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from service.auth_service import AuthService
from db.services.user_service import UserService
from db.main import get_db_session_context
from logs.log_store import get_logger

logger = get_logger(__name__)

# Simple security scheme
security = HTTPBearer()


def get_auth_service() -> AuthService:
    """Simple dependency to get AuthService."""
    with get_db_session_context() as db:
        user_service = UserService(db)
        return AuthService(user_service)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Simple dependency to get current user from JWT token."""
    try:
        token = credentials.credentials
        user = auth_service.get_user_from_token(token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return user
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


def get_current_user_optional(
    request: Request,
    guest_cookie: Optional[str] = Header(None, alias="X-Guest-Cookie"),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Simple dependency for optional authentication.
    
    Returns user if JWT token is valid, None if guest cookie is valid.
    """
    # Try JWT token first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            user = auth_service.get_user_from_token(token)
            if user:
                return user
        except Exception:
            pass
    
    # Try guest cookie
    if guest_cookie and auth_service.validate_guest_cookie(guest_cookie):
        return None  # Guest user
    
    # No valid authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )


def get_admin_user(
    current_user = Depends(get_current_user)
):
    """Simple dependency to check admin access."""
    # Simple admin check - in real app this would check user roles
    if not current_user or not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    logger.info(f"Admin access granted for user: {current_user.id}")
    return current_user


def validate_guest_or_user(
    guest_cookie: Optional[str] = Header(None, alias="X-Guest-Cookie"),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Simple validation for guest cookie or user token."""
    if guest_cookie and auth_service.validate_guest_cookie(guest_cookie):
        return {"type": "guest", "cookie": guest_cookie}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid authentication required"
    )