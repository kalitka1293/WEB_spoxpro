# Middleware Documentation

Simple middleware for spoXpro backend authentication and authorization.

## Files

### auth_middleware.py
- `auth_middleware()` - Validates JWT tokens and guest cookies
- `admin_middleware()` - Checks admin access for /admin routes
- Simple validation functions

### dependencies.py
- `get_current_user()` - Get authenticated user (required)
- `get_current_user_optional()` - Get user or allow guest
- `get_admin_user()` - Require admin access
- `validate_guest_or_user()` - Validate guest cookie or user token

### exception_handlers.py
- Global exception handlers for consistent error responses
- Custom business logic exceptions
- HTTP error mapping

## Usage

### In routes (simple):
```python
from middleware.dependencies import get_current_user, get_admin_user

@router.get("/protected")
async def protected_route(user = Depends(get_current_user)):
    return {"user_id": user.id}

@router.get("/admin")
async def admin_route(admin = Depends(get_admin_user)):
    return {"admin_id": admin.id}
```

### Public routes:
- `/` - Root
- `/health` - Health check
- `/docs` - API docs
- `/auth/*` - Authentication endpoints
- `/store/*` - Public store endpoints

### Protected routes:
- `/user/*` - User endpoints (JWT or guest cookie)
- `/admin/*` - Admin endpoints (JWT + admin check)

## Simple and reliable design
- No complex logic
- Clear error messages
- Easy to understand and maintain