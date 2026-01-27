"""
Authentication business logic service for spoXpro backend.

This service provides comprehensive authentication functionality including:
- User registration with password hashing
- JWT token generation and validation
- Guest cookie generation and management
- Email verification code handling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import secrets
import string
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import get_settings
from db.services.user_service import UserService
from db.models.user import User
from logs.log_store import get_logger
from middleware.exception_handlers import (
    AuthenticationError, AuthorizationError, ResourceNotFoundError, 
    InvalidOperationError, BusinessLogicError
)

logger = get_logger(__name__)
settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service class for authentication business logic."""
    
    def __init__(self, user_service: UserService):
        """
        Initialize the AuthService with a user service.
        
        Args:
            user_service: UserService instance for database operations
        """
        self.user_service = user_service
    
    # ==================== USER REGISTRATION ====================
    
    def register_user(self, email: str, password: str, phone: str, cookie: Optional[str] = None) -> Optional[User]:
        """
        Register a new user with password hashing.
        
        Args:
            email: User's email address
            password: Plain text password
            phone: User's phone number
            cookie: Optional guest cookie to associate with the user
        
        Returns:
            User: Created user object or None if registration failed
        
        Raises:
            ValueError: If email already exists or validation fails
        """
        try:
            # Check if email already exists
            if self.user_service.email_exists(email):
                logger.warning(f"Registration failed - email already exists: {email}")
                raise ValueError("Email address is already registered")
            
            # Validate password strength
            self._validate_password_strength(password)
            
            # Create user data
            user_data = {
                "email": email,
                "password": password,  # Will be hashed by user_service
                "phone": phone,
                "cookie": cookie
            }
            
            # Create user
            user = self.user_service.create_user(user_data)
            if not user:
                logger.error(f"Failed to create user during registration: {email}")
                raise ValueError("Failed to create user account")
            
            logger.info(f"User registered successfully: {email}")
            return user
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during user registration for {email}: {str(e)}")
            raise ValueError("Registration failed due to system error")
    
    def _validate_password_strength(self, password: str) -> None:
        """
        Validate password strength requirements.
        
        Args:
            password: Password to validate
        
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if len(password) > 128:
            raise ValueError("Password must be no more than 128 characters long")
        
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)
        
        if not has_letter:
            raise ValueError("Password must contain at least one letter")
        if not has_number:
            raise ValueError("Password must contain at least one number")
    
    # ==================== USER AUTHENTICATION ====================
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email address
            password: Plain text password
        
        Returns:
            User: User object if authentication successful, None otherwise
        """
        try:
            user = self.user_service.authenticate_user(email, password)
            if user:
                logger.info(f"User authentication successful: {email}")
            else:
                logger.warning(f"User authentication failed: {email}")
            return user
        except Exception as e:
            logger.error(f"Error during user authentication for {email}: {str(e)}")
            return None
    
    # ==================== JWT TOKEN MANAGEMENT ====================
    
    def generate_jwt_token(self, user: User) -> Dict[str, Any]:
        """
        Generate a JWT access token for a user.
        
        Args:
            user: User object
        
        Returns:
            Dict containing token information:
                - access_token: JWT token string
                - token_type: "bearer"
                - user_id: User's ID
                - email: User's email
                - expires_in: Token expiration time in seconds
        """
        try:
            # Calculate expiration time
            expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
            expires_at = datetime.utcnow() + expires_delta
            
            # Create JWT payload
            payload = {
                "sub": str(user.id),  # Subject (user ID)
                "email": user.email,
                "exp": expires_at,
                "iat": datetime.utcnow(),  # Issued at
                "type": "access_token"
            }
            
            # Generate token
            token = jwt.encode(
                payload,
                settings.jwt_secret_key,
                algorithm=settings.jwt_algorithm
            )
            
            logger.info(f"JWT token generated for user: {user.email}")
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "user_id": user.id,
                "email": user.email,
                "expires_in": settings.jwt_access_token_expire_minutes * 60
            }
            
        except Exception as e:
            logger.error(f"Error generating JWT token for user {user.email}: {str(e)}")
            raise ValueError("Failed to generate authentication token")
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token and extract user information.
        
        Args:
            token: JWT token string
        
        Returns:
            Dict containing user information if valid:
                - user_id: User's ID
                - email: User's email
                - expires_at: Token expiration datetime
            None if token is invalid or expired
        """
        try:
            # Decode and validate token
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            
            # Extract user information
            user_id = int(payload.get("sub"))
            email = payload.get("email")
            expires_at = datetime.fromtimestamp(payload.get("exp"))
            
            # Verify user still exists
            user = self.user_service.get_user_by_id(user_id)
            if not user:
                logger.warning(f"JWT token validation failed - user not found: {user_id}")
                return None
            
            # Verify email matches (in case user changed email)
            if user.email != email:
                logger.warning(f"JWT token validation failed - email mismatch for user: {user_id}")
                return None
            
            logger.debug(f"JWT token validated successfully for user: {email}")
            
            return {
                "user_id": user_id,
                "email": email,
                "expires_at": expires_at
            }
            
        except JWTError as e:
            logger.debug(f"JWT token validation failed - invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error validating JWT token: {str(e)}")
            return None
    
    def get_user_from_token(self, token: str) -> Optional[User]:
        """
        Get user object from JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            User: User object if token is valid, None otherwise
        """
        token_data = self.validate_jwt_token(token)
        if not token_data:
            return None
        
        return self.user_service.get_user_by_id(token_data["user_id"])
    
    # ==================== GUEST COOKIE MANAGEMENT ====================
    
    def generate_guest_cookie(self) -> Dict[str, Any]:
        """
        Generate a unique guest cookie for anonymous users.
        
        Returns:
            Dict containing cookie information:
                - cookie: Unique cookie string
                - expires_at: Cookie expiration datetime
        """
        try:
            # Generate secure random cookie
            cookie_length = 32
            cookie = "guest_" + ''.join(
                secrets.choice(string.ascii_letters + string.digits)
                for _ in range(cookie_length)
            )
            
            # Calculate expiration time
            expires_at = datetime.utcnow() + timedelta(seconds=settings.cookie_max_age)
            
            logger.info(f"Guest cookie generated: {cookie[:12]}...")
            
            return {
                "cookie": cookie,
                "expires_at": expires_at
            }
            
        except Exception as e:
            logger.error(f"Error generating guest cookie: {str(e)}")
            raise ValueError("Failed to generate guest cookie")
    
    def validate_guest_cookie(self, cookie: str) -> bool:
        """
        Validate a guest cookie format.
        
        Args:
            cookie: Cookie string to validate
        
        Returns:
            bool: True if cookie format is valid, False otherwise
        """
        try:
            # Check basic format
            if not cookie or not isinstance(cookie, str):
                return False
            
            # Check prefix
            if not cookie.startswith("guest_"):
                return False
            
            # Check length (guest_ + 32 characters)
            if len(cookie) != 38:
                return False
            
            # Check characters (alphanumeric only after prefix)
            cookie_part = cookie[6:]  # Remove "guest_" prefix
            if not cookie_part.isalnum():
                return False
            
            logger.debug(f"Guest cookie validation successful: {cookie[:12]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error validating guest cookie: {str(e)}")
            return False
    
    # ==================== EMAIL VERIFICATION ====================
    
    def send_verification_code(self, email: str) -> str:
        """
        Generate and store a verification code for email verification.
        
        Args:
            email: Email address to send verification code to
        
        Returns:
            str: Generated verification code
        
        Raises:
            ValueError: If code generation fails
        """
        try:
            # Generate 6-digit verification code
            code = ''.join(secrets.choice(string.digits) for _ in range(6))
            
            # Store code in database
            success = self.user_service.create_verification_code(email, code)
            if not success:
                logger.error(f"Failed to store verification code for email: {email}")
                raise ValueError("Failed to generate verification code")
            
            logger.info(f"Verification code generated for email: {email}")
            
            # In a real application, you would send the code via email here
            # For now, we'll just return it (in production, this should be sent via email service)
            return code
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating verification code for {email}: {str(e)}")
            raise ValueError("Failed to generate verification code")
    
    def verify_email_code(self, email: str, code: str) -> bool:
        """
        Verify an email verification code.
        
        Args:
            email: Email address
            code: Verification code to check
        
        Returns:
            bool: True if code is valid and not expired, False otherwise
        """
        try:
            result = self.user_service.verify_code(email, code)
            if result:
                logger.info(f"Email verification successful for: {email}")
            else:
                logger.warning(f"Email verification failed for: {email}")
            return result
        except Exception as e:
            logger.error(f"Error verifying email code for {email}: {str(e)}")
            return False
    
    # ==================== PASSWORD MANAGEMENT ====================
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            user_id: User's ID
            current_password: Current password for verification
            new_password: New password to set
        
        Returns:
            bool: True if password was changed successfully, False otherwise
        
        Raises:
            ValueError: If validation fails
        """
        try:
            # Get user
            user = self.user_service.get_user_by_id(user_id)
            if not user:
                logger.warning(f"Password change failed - user not found: {user_id}")
                raise ValueError("User not found")
            
            # Verify current password
            if not self.user_service.verify_password(current_password, user.password_hash):
                logger.warning(f"Password change failed - invalid current password for user: {user_id}")
                raise ValueError("Current password is incorrect")
            
            # Validate new password strength
            self._validate_password_strength(new_password)
            
            # Update password
            success = self.user_service.update_user(user_id, {"password": new_password})
            if not success:
                logger.error(f"Failed to update password for user: {user_id}")
                raise ValueError("Failed to update password")
            
            logger.info(f"Password changed successfully for user: {user_id}")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error changing password for user {user_id}: {str(e)}")
            raise ValueError("Password change failed due to system error")
    
    def reset_password_with_code(self, email: str, code: str, new_password: str) -> bool:
        """
        Reset a user's password using a verification code.
        
        Args:
            email: User's email address
            code: Verification code
            new_password: New password to set
        
        Returns:
            bool: True if password was reset successfully, False otherwise
        
        Raises:
            ValueError: If validation fails
        """
        try:
            # Verify the code first
            if not self.verify_email_code(email, code):
                logger.warning(f"Password reset failed - invalid code for email: {email}")
                raise ValueError("Invalid or expired verification code")
            
            # Get user by email
            user = self.user_service.get_user_by_email(email)
            if not user:
                logger.warning(f"Password reset failed - user not found: {email}")
                raise ValueError("User not found")
            
            # Validate new password strength
            self._validate_password_strength(new_password)
            
            # Update password
            success = self.user_service.update_user(user.id, {"password": new_password})
            if not success:
                logger.error(f"Failed to reset password for user: {email}")
                raise ValueError("Failed to reset password")
            
            logger.info(f"Password reset successfully for user: {email}")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error resetting password for {email}: {str(e)}")
            raise ValueError("Password reset failed due to system error")
    
    # ==================== UTILITY METHODS ====================
    
    def cleanup_expired_codes(self) -> int:
        """
        Clean up expired verification codes.
        
        Returns:
            int: Number of codes cleaned up
        """
        try:
            count = self.user_service.cleanup_expired_codes()
            if count > 0:
                logger.info(f"Cleaned up {count} expired verification codes")
            return count
        except Exception as e:
            logger.error(f"Error cleaning up expired codes: {str(e)}")
            return 0
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user profile information (safe for API responses).
        
        Args:
            user_id: User's ID
        
        Returns:
            Dict containing safe user information or None if user not found
        """
        try:
            user = self.user_service.get_user_by_id(user_id)
            if not user:
                return None
            
            return {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "created_date": user.created_date
            }
        except Exception as e:
            logger.error(f"Error getting user profile for {user_id}: {str(e)}")
            return None