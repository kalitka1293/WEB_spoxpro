"""
Authentication endpoints for spoXpro backend.
Handles user registration, login, verification, and guest cookie management.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from db.main import get_db_session_context
from db.services.user_service import UserService
from service.auth_service import AuthService
from DTO.auth import (
    UserRegistrationRequest, UserLoginRequest, AuthResponse,
    GuestCookieRequest, GuestCookieResponse, VerificationCodeRequest,
    VerifyCodeRequest, TokenValidationRequest, TokenValidationResponse,
    PasswordResetRequest, PasswordResetConfirmRequest, AuthErrorResponse,
    UserProfileResponse, UpdateProfileRequest
)
from logs.log_store import get_logger

logger = get_logger(__name__)

# Create router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["authentication"])

# Security scheme for JWT tokens
security = HTTPBearer()


def get_auth_service() -> AuthService:
    """Dependency to get AuthService instance."""
    with get_db_session_context() as db:
        user_service = UserService(db)
        return AuthService(user_service)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Dependency to get current authenticated user from JWT token."""
    try:
        token = credentials.credentials
        user = auth_service.get_user_from_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Register a new user account with email, password, and phone number. Returns JWT token on success.",
    responses={
        201: {"description": "User registered successfully"},
        400: {"model": AuthErrorResponse, "description": "Invalid input data"},
        409: {"model": AuthErrorResponse, "description": "Email already exists"}
    }
)
async def register_user(
    request: UserRegistrationRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user account."""
    try:
        # Register user
        user = auth_service.register_user(
            email=request.email,
            password=request.password,
            phone=request.phone
        )
        
        # Generate JWT token
        token_data = auth_service.generate_jwt_token(user)
        
        logger.info(f"User registration successful: {request.email}")
        return AuthResponse(**token_data)
        
    except ValueError as e:
        error_message = str(e)
        if "already registered" in error_message:
            logger.warning(f"Registration failed - email exists: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "email_exists", "message": error_message}
            )
        else:
            logger.warning(f"Registration failed - validation error: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "validation_error", "message": error_message}
            )
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "registration_failed", "message": "Registration failed due to system error"}
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="User login",
    description="Authenticate user with email and password. Returns JWT token on success.",
    responses={
        200: {"description": "Login successful"},
        401: {"model": AuthErrorResponse, "description": "Invalid credentials"},
        400: {"model": AuthErrorResponse, "description": "Invalid input data"}
    }
)
async def login_user(
    request: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user and return JWT token."""
    try:
        # Authenticate user
        user = auth_service.authenticate_user(request.email, request.password)
        if not user:
            logger.warning(f"Login failed - invalid credentials: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_credentials", "message": "Invalid email or password"}
            )
        
        # Generate JWT token
        token_data = auth_service.generate_jwt_token(user)
        
        logger.info(f"User login successful: {request.email}")
        return AuthResponse(**token_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "login_failed", "message": "Login failed due to system error"}
        )


@router.post(
    "/guest-cookie",
    response_model=GuestCookieResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate guest cookie",
    description="Generate a unique cookie for guest users to track their cart and session.",
    responses={
        201: {"description": "Guest cookie generated successfully"},
        500: {"model": AuthErrorResponse, "description": "Cookie generation failed"}
    }
)
async def generate_guest_cookie(
    request: Optional[GuestCookieRequest] = None,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Generate a guest cookie for anonymous users."""
    try:
        cookie_data = auth_service.generate_guest_cookie()
        
        logger.info(f"Guest cookie generated: {cookie_data['cookie'][:12]}...")
        return GuestCookieResponse(**cookie_data)
        
    except Exception as e:
        logger.error(f"Error generating guest cookie: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "cookie_generation_failed", "message": "Failed to generate guest cookie"}
        )


@router.post(
    "/send-verification",
    status_code=status.HTTP_200_OK,
    summary="Send verification code",
    description="Send a verification code to the specified email address.",
    responses={
        200: {"description": "Verification code sent successfully"},
        400: {"model": AuthErrorResponse, "description": "Invalid email address"},
        500: {"model": AuthErrorResponse, "description": "Failed to send verification code"}
    }
)
async def send_verification_code(
    request: VerificationCodeRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Send a verification code to an email address."""
    try:
        code = auth_service.send_verification_code(request.email)
        
        logger.info(f"Verification code sent to: {request.email}")
        
        # In production, the code would be sent via email
        # For development/testing, we return it in the response
        return {
            "message": "Verification code sent successfully",
            "code": code  # Remove this in production!
        }
        
    except ValueError as e:
        logger.warning(f"Failed to send verification code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "verification_failed", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error sending verification code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "verification_failed", "message": "Failed to send verification code"}
        )


@router.post(
    "/verify",
    status_code=status.HTTP_200_OK,
    summary="Verify email code",
    description="Verify an email verification code.",
    responses={
        200: {"description": "Code verified successfully"},
        400: {"model": AuthErrorResponse, "description": "Invalid or expired code"},
        500: {"model": AuthErrorResponse, "description": "Verification failed"}
    }
)
async def verify_email_code(
    request: VerifyCodeRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Verify an email verification code."""
    try:
        is_valid = auth_service.verify_email_code(request.email, request.code)
        
        if not is_valid:
            logger.warning(f"Email verification failed: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_code", "message": "Invalid or expired verification code"}
            )
        
        logger.info(f"Email verification successful: {request.email}")
        return {"message": "Email verified successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during email verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "verification_failed", "message": "Email verification failed"}
        )


@router.post(
    "/validate",
    response_model=TokenValidationResponse,
    summary="Validate JWT token",
    description="Validate a JWT token and return user information if valid.",
    responses={
        200: {"description": "Token validation result"},
        400: {"model": AuthErrorResponse, "description": "Invalid request"},
        500: {"model": AuthErrorResponse, "description": "Validation failed"}
    }
)
async def validate_token(
    request: TokenValidationRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Validate a JWT token."""
    try:
        token_data = auth_service.validate_jwt_token(request.token)
        
        if token_data:
            logger.debug(f"Token validation successful for user: {token_data['email']}")
            return TokenValidationResponse(
                valid=True,
                user_id=token_data["user_id"],
                email=token_data["email"],
                expires_at=token_data["expires_at"]
            )
        else:
            logger.debug("Token validation failed - invalid token")
            return TokenValidationResponse(valid=False)
            
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "validation_failed", "message": "Token validation failed"}
        )


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Send a password reset code to the specified email address.",
    responses={
        200: {"description": "Password reset code sent successfully"},
        404: {"model": AuthErrorResponse, "description": "Email not found"},
        500: {"model": AuthErrorResponse, "description": "Failed to send reset code"}
    }
)
async def request_password_reset(
    request: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Request a password reset code."""
    try:
        # Check if user exists
        with get_db_session_context() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_email(request.email)
            if not user:
                logger.warning(f"Password reset requested for non-existent email: {request.email}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "email_not_found", "message": "Email address not found"}
                )
        
        # Send verification code
        code = auth_service.send_verification_code(request.email)
        
        logger.info(f"Password reset code sent to: {request.email}")
        
        # In production, the code would be sent via email
        # For development/testing, we return it in the response
        return {
            "message": "Password reset code sent successfully",
            "code": code  # Remove this in production!
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error requesting password reset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "reset_failed", "message": "Failed to send password reset code"}
        )


@router.post(
    "/reset-password-confirm",
    status_code=status.HTTP_200_OK,
    summary="Confirm password reset",
    description="Reset password using verification code.",
    responses={
        200: {"description": "Password reset successfully"},
        400: {"model": AuthErrorResponse, "description": "Invalid code or password"},
        500: {"model": AuthErrorResponse, "description": "Password reset failed"}
    }
)
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Confirm password reset with verification code."""
    try:
        success = auth_service.reset_password_with_code(
            request.email,
            request.code,
            request.new_password
        )
        
        if not success:
            logger.warning(f"Password reset confirmation failed: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "reset_failed", "message": "Password reset failed"}
            )
        
        logger.info(f"Password reset successful: {request.email}")
        return {"message": "Password reset successfully"}
        
    except ValueError as e:
        logger.warning(f"Password reset validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": str(e)}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during password reset confirmation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "reset_failed", "message": "Password reset failed due to system error"}
        )


@router.get(
    "/profile",
    response_model=UserProfileResponse,
    summary="Get user profile",
    description="Get current user's profile information. Requires authentication.",
    responses={
        200: {"description": "User profile retrieved successfully"},
        401: {"model": AuthErrorResponse, "description": "Authentication required"},
        404: {"model": AuthErrorResponse, "description": "User not found"}
    }
)
async def get_user_profile(
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current user's profile information."""
    try:
        profile = auth_service.get_user_profile(current_user.id)
        if not profile:
            logger.error(f"Profile not found for authenticated user: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "profile_not_found", "message": "User profile not found"}
            )
        
        logger.debug(f"Profile retrieved for user: {current_user.email}")
        return UserProfileResponse(**profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "profile_error", "message": "Failed to retrieve user profile"}
        )


@router.put(
    "/profile",
    response_model=UserProfileResponse,
    summary="Update user profile",
    description="Update current user's profile information. Requires authentication.",
    responses={
        200: {"description": "Profile updated successfully"},
        400: {"model": AuthErrorResponse, "description": "Invalid input data"},
        401: {"model": AuthErrorResponse, "description": "Authentication required"},
        404: {"model": AuthErrorResponse, "description": "User not found"}
    }
)
async def update_user_profile(
    request: UpdateProfileRequest,
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update current user's profile information."""
    try:
        updates = {}
        
        # Update phone if provided
        if request.phone is not None:
            updates["phone"] = request.phone
        
        # Handle password change if provided
        if request.new_password is not None:
            if not request.current_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "validation_error", "message": "Current password is required for password change"}
                )
            
            # Change password using auth service
            success = auth_service.change_password(
                current_user.id,
                request.current_password,
                request.new_password
            )
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "password_change_failed", "message": "Failed to change password"}
                )
        
        # Update other fields if any
        if updates:
            with get_db_session_context() as db:
                user_service = UserService(db)
                updated_user = user_service.update_user(current_user.id, updates)
                if not updated_user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={"error": "update_failed", "message": "Failed to update profile"}
                    )
        
        # Get updated profile
        profile = auth_service.get_user_profile(current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "profile_not_found", "message": "User profile not found"}
            )
        
        logger.info(f"Profile updated for user: {current_user.email}")
        return UserProfileResponse(**profile)
        
    except ValueError as e:
        logger.warning(f"Profile update validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": str(e)}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "update_failed", "message": "Profile update failed due to system error"}
        )