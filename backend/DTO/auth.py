"""
Authentication-related Pydantic DTO models for spoXpro backend.

These models define the request and response structures for authentication endpoints,
including user registration, login, verification, and guest cookie management.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class UserRegistrationRequest(BaseModel):
    """Request model for user registration."""
    
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=128, description="User's password (minimum 8 characters)")
    phone: str = Field(..., min_length=10, max_length=20, description="User's phone number")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)
        
        if not has_letter:
            raise ValueError('Password must contain at least one letter')
        if not has_number:
            raise ValueError('Password must contain at least one number')
        
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        # Remove common phone number characters
        cleaned = ''.join(c for c in v if c.isdigit() or c in '+()-. ')
        
        # Check if it contains at least 10 digits
        digits = ''.join(c for c in cleaned if c.isdigit())
        if len(digits) < 10:
            raise ValueError('Phone number must contain at least 10 digits')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "phone": "+1234567890"
            }
        }


class UserLoginRequest(BaseModel):
    """Request model for user login."""
    
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class AuthResponse(BaseModel):
    """Response model for successful authentication."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: int = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": 123,
                "email": "user@example.com",
                "expires_in": 3600
            }
        }


class GuestCookieRequest(BaseModel):
    """Request model for generating guest cookie (optional parameters)."""
    
    user_agent: Optional[str] = Field(None, description="User agent string for tracking")
    
    class Config:
        schema_extra = {
            "example": {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        }


class GuestCookieResponse(BaseModel):
    """Response model for guest cookie generation."""
    
    cookie: str = Field(..., description="Unique guest cookie identifier")
    expires_at: datetime = Field(..., description="Cookie expiration timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "cookie": "guest_abc123def456ghi789",
                "expires_at": "2024-12-31T23:59:59Z"
            }
        }


class VerificationCodeRequest(BaseModel):
    """Request model for sending verification code."""
    
    email: EmailStr = Field(..., description="Email address to send verification code to")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class VerifyCodeRequest(BaseModel):
    """Request model for verifying a code."""
    
    email: EmailStr = Field(..., description="Email address associated with the code")
    code: str = Field(..., min_length=4, max_length=10, description="Verification code")
    
    @validator('code')
    def validate_code(cls, v):
        """Validate verification code format."""
        # Remove whitespace and ensure it's alphanumeric
        cleaned = v.strip()
        if not cleaned.isalnum():
            raise ValueError('Verification code must contain only letters and numbers')
        return cleaned
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "code": "123456"
            }
        }


class TokenValidationRequest(BaseModel):
    """Request model for token validation."""
    
    token: str = Field(..., description="JWT token to validate")
    
    class Config:
        schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class TokenValidationResponse(BaseModel):
    """Response model for token validation."""
    
    valid: bool = Field(..., description="Whether the token is valid")
    user_id: Optional[int] = Field(None, description="User ID if token is valid")
    email: Optional[str] = Field(None, description="User email if token is valid")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")
    
    class Config:
        schema_extra = {
            "example": {
                "valid": True,
                "user_id": 123,
                "email": "user@example.com",
                "expires_at": "2024-12-31T23:59:59Z"
            }
        }


class PasswordResetRequest(BaseModel):
    """Request model for password reset."""
    
    email: EmailStr = Field(..., description="Email address for password reset")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirmRequest(BaseModel):
    """Request model for confirming password reset."""
    
    email: EmailStr = Field(..., description="Email address")
    code: str = Field(..., min_length=4, max_length=10, description="Reset code")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)
        
        if not has_letter:
            raise ValueError('Password must contain at least one letter')
        if not has_number:
            raise ValueError('Password must contain at least one number')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "code": "123456",
                "new_password": "newsecurepassword123"
            }
        }


class AuthErrorResponse(BaseModel):
    """Response model for authentication errors."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "invalid_credentials",
                "message": "Invalid email or password",
                "details": {
                    "field": "password",
                    "code": "INVALID_PASSWORD"
                }
            }
        }


class UserProfileResponse(BaseModel):
    """Response model for user profile information."""
    
    id: int = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")
    phone: str = Field(..., description="User's phone number")
    created_date: datetime = Field(..., description="Account creation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 123,
                "email": "user@example.com",
                "phone": "+1234567890",
                "created_date": "2024-01-01T12:00:00Z"
            }
        }


class UpdateProfileRequest(BaseModel):
    """Request model for updating user profile."""
    
    phone: Optional[str] = Field(None, min_length=10, max_length=20, description="New phone number")
    current_password: Optional[str] = Field(None, description="Current password (required for password change)")
    new_password: Optional[str] = Field(None, min_length=8, max_length=128, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v, values):
        """Validate new password if provided."""
        if v is not None:
            # If new password is provided, current password must also be provided
            if 'current_password' not in values or not values['current_password']:
                raise ValueError('Current password is required when changing password')
            
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters long')
            
            # Check for at least one letter and one number
            has_letter = any(c.isalpha() for c in v)
            has_number = any(c.isdigit() for c in v)
            
            if not has_letter:
                raise ValueError('Password must contain at least one letter')
            if not has_number:
                raise ValueError('Password must contain at least one number')
        
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format if provided."""
        if v is not None:
            # Remove common phone number characters
            cleaned = ''.join(c for c in v if c.isdigit() or c in '+()-. ')
            
            # Check if it contains at least 10 digits
            digits = ''.join(c for c in cleaned if c.isdigit())
            if len(digits) < 10:
                raise ValueError('Phone number must contain at least 10 digits')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "phone": "+1987654321",
                "current_password": "oldpassword123",
                "new_password": "newpassword456"
            }
        }