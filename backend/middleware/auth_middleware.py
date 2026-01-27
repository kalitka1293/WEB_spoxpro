"""
Authentication and authorization middleware for spoXpro backend.

Simple middleware for JWT token validation and admin authorization.
"""

from fastapi import Request, HTTPException, status
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
    """Get auth service instance."""
    with get_db_session_context() as db:
        user_service = UserService(db)
        return AuthService(user_service)


def get_current_user_from_token(token: str):
    """Get user from JWT token."""
    try:
        auth_service = get_auth_service()
        user = auth_service.get_user_from_token(token)
        return user
    except Exception as e:
        logger.error(f"Error getting user from token: {e}")
        return None


def validate_jwt_token(token: str) -> bool:
    """Simple JWT token validation."""
    try:
        auth_service = get_auth_service()
        token_data = auth_service.validate_jwt_token(token)
        return token_data is not None
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return False


def validate_guest_cookie(cookie: str) -> bool:
    """Simple guest cookie validation."""
    try:
        auth_service = get_auth_service()
        return auth_service.validate_guest_cookie(cookie)
    except Exception as e:
        logger.error(f"Cookie validation error: {e}")
        return False


def check_admin_access(user) -> bool:
    """Check if user has admin access."""
    if not user:
        return False
    
    # Simple admin check - in real app this would check user roles
    # For now, just check if user exists and is valid
    return user.id is not None


async def auth_middleware(request: Request, call_next):
    """
    Simple authentication middleware.
    
    Validates JWT tokens and guest cookies for protected routes.
    """
    path = request.url.path
    method = request.method
    
    # Skip auth for public routes
    public_routes = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/auth/register",
        "/auth/login",
        "/auth/guest-cookie",
        "/store/products",
        "/store/categories",
        "/store/product-types",
        "/store/sport-types",
        "/store/materials",
        "/store/statistics",
        "/store/search"
    ]
    
    # Check if route is public
    is_public = False
    for public_route in public_routes:
        if path.startswith(public_route):
            is_public = True
            break
    
    if is_public:
        response = await call_next(request)
        return response
    
    # Check for JWT token in Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        if validate_jwt_token(token):
            # Add user to request state
            user = get_current_user_from_token(token)
            request.state.user = user
            request.state.auth_type = "jwt"
            response = await call_next(request)
            return response
    
    # Check for guest cookie in header
    guest_cookie = request.headers.get("X-Guest-Cookie")
    if guest_cookie and validate_guest_cookie(guest_cookie):
        # Allow guest access for cart operations
        if path.startswith("/user/cart"):
            request.state.user = None
            request.state.auth_type = "guest"
            request.state.guest_cookie = guest_cookie
            response = await call_next(request)
            return response
    
    # No valid authentication found
    logger.warning(f"Unauthorized access attempt: {method} {path}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"}
    )


async def admin_middleware(request: Request, call_next):
    """
    Simple admin authorization middleware.
    
    Checks if user has admin access for admin routes.
    """
    path = request.url.path
    
    # Check if this is an admin route
    if not path.startswith("/admin"):
        response = await call_next(request)
        return response
    
    # Get user from request state (set by auth_middleware)
    user = getattr(request.state, "user", None)
    
    # Check admin access
    if not check_admin_access(user):
        logger.warning(f"Admin access denied for user: {user.id if user else 'None'}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    logger.info(f"Admin access granted for user: {user.id}")
    response = await call_next(request)
    return response