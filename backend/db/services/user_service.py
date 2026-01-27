"""
User database service for spoXpro backend.

This service provides comprehensive CRUD operations for users and verification codes,
including user authentication, password management, and email verification.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import bcrypt

from db.models.user import User, VerificationCode
from logs.log_store import get_logger

logger = get_logger(__name__)


class UserService:
    """Service class for user-related database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the UserService with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    # ==================== USER CRUD OPERATIONS ====================
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[User]:
        """
        Create a new user with hashed password.
        
        Args:
            user_data: Dictionary containing user information:
                - email: str (required, unique)
                - password: str (required, will be hashed)
                - phone: str (required)
                - cookie: str (optional, for guest users)
        
        Returns:
            User: Created user object or None if creation failed
        
        Raises:
            IntegrityError: If email already exists
        """
        try:
            # Hash the password
            hashed_password = self.hash_password(user_data["password"])
            
            # Create user object
            user = User(
                email=user_data["email"],
                password_hash=hashed_password,
                phone=user_data["phone"],
                cookie=user_data.get("cookie"),
                created_date=datetime.utcnow()
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User created successfully with ID: {user.id}")
            return user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create user - email already exists: {user_data.get('email')}")
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating user: {str(e)}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating user: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve a user by their ID.
        
        Args:
            user_id: The user's ID
        
        Returns:
            User: User object or None if not found
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                logger.debug(f"User found with ID: {user_id}")
            else:
                logger.debug(f"User not found with ID: {user_id}")
            return user
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving user by ID {user_id}: {str(e)}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.
        
        Args:
            email: The user's email address
        
        Returns:
            User: User object or None if not found
        """
        try:
            user = self.db.query(User).filter(User.email == email).first()
            if user:
                logger.debug(f"User found with email: {email}")
            else:
                logger.debug(f"User not found with email: {email}")
            return user
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving user by email {email}: {str(e)}")
            return None
    
    def get_user_by_cookie(self, cookie: str) -> Optional[User]:
        """
        Retrieve a user by their cookie value.
        
        Args:
            cookie: The user's cookie value
        
        Returns:
            User: User object or None if not found
        """
        try:
            user = self.db.query(User).filter(User.cookie == cookie).first()
            if user:
                logger.debug(f"User found with cookie: {cookie[:8]}...")
            else:
                logger.debug(f"User not found with cookie: {cookie[:8]}...")
            return user
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving user by cookie: {str(e)}")
            return None
    
    def update_user(self, user_id: int, updates: Dict[str, Any]) -> Optional[User]:
        """
        Update user information.
        
        Args:
            user_id: The user's ID
            updates: Dictionary of fields to update
        
        Returns:
            User: Updated user object or None if update failed
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                logger.warning(f"Cannot update user - user not found with ID: {user_id}")
                return None
            
            # Update allowed fields
            allowed_fields = ["email", "phone", "cookie"]
            for field, value in updates.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)
            
            # Handle password update separately (needs hashing)
            if "password" in updates:
                user.password_hash = self.hash_password(updates["password"])
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User updated successfully with ID: {user_id}")
            return user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to update user - integrity constraint: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating user {user_id}: {str(e)}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error updating user {user_id}: {str(e)}")
            return None
    
    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user by their ID.
        
        Args:
            user_id: The user's ID
        
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                logger.warning(f"Cannot delete user - user not found with ID: {user_id}")
                return False
            
            self.db.delete(user)
            self.db.commit()
            
            logger.info(f"User deleted successfully with ID: {user_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deleting user {user_id}: {str(e)}")
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error deleting user {user_id}: {str(e)}")
            return False
    
    # ==================== PASSWORD MANAGEMENT ====================
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
        
        Returns:
            str: Hashed password
        """
        # Truncate password to 72 bytes for bcrypt compatibility
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
        
        Returns:
            bool: True if password matches, False otherwise
        """
        # Truncate password to 72 bytes for bcrypt compatibility
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
            
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
    
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
            user = self.get_user_by_email(email)
            if not user:
                logger.debug(f"Authentication failed - user not found: {email}")
                return None
            
            if not self.verify_password(password, user.password_hash):
                logger.debug(f"Authentication failed - invalid password: {email}")
                return None
            
            logger.info(f"User authenticated successfully: {email}")
            return user
            
        except Exception as e:
            logger.error(f"Error during authentication for {email}: {str(e)}")
            return None
    
    # ==================== VERIFICATION CODE MANAGEMENT ====================
    
    def create_verification_code(self, email: str, code: str, expires_in_minutes: int = 15) -> bool:
        """
        Create a verification code for an email address.
        
        Args:
            email: Email address to associate with the code
            code: Verification code
            expires_in_minutes: Code expiration time in minutes (default: 15)
        
        Returns:
            bool: True if code was created successfully, False otherwise
        """
        try:
            # Delete any existing codes for this email
            self.db.query(VerificationCode).filter(
                VerificationCode.email == email
            ).delete()
            
            # Create new verification code
            expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
            verification_code = VerificationCode(
                email=email,
                code=code,
                created_date=datetime.utcnow(),
                expires_at=expires_at
            )
            
            self.db.add(verification_code)
            self.db.commit()
            
            logger.info(f"Verification code created for email: {email}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating verification code for {email}: {str(e)}")
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating verification code for {email}: {str(e)}")
            return False
    
    def verify_code(self, email: str, code: str) -> bool:
        """
        Verify a code for an email address.
        
        Args:
            email: Email address
            code: Verification code to check
        
        Returns:
            bool: True if code is valid and not expired, False otherwise
        """
        try:
            verification_code = self.db.query(VerificationCode).filter(
                VerificationCode.email == email,
                VerificationCode.code == code
            ).first()
            
            if not verification_code:
                logger.debug(f"Verification failed - code not found for email: {email}")
                return False
            
            # Check if code has expired
            if datetime.utcnow() > verification_code.expires_at:
                logger.debug(f"Verification failed - code expired for email: {email}")
                # Clean up expired code
                self.db.delete(verification_code)
                self.db.commit()
                return False
            
            # Code is valid, delete it (one-time use)
            self.db.delete(verification_code)
            self.db.commit()
            
            logger.info(f"Verification code validated successfully for email: {email}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error verifying code for {email}: {str(e)}")
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error verifying code for {email}: {str(e)}")
            return False
    
    def cleanup_expired_codes(self) -> int:
        """
        Clean up expired verification codes.
        
        Returns:
            int: Number of codes deleted
        """
        try:
            deleted_count = self.db.query(VerificationCode).filter(
                VerificationCode.expires_at < datetime.utcnow()
            ).delete()
            
            self.db.commit()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired verification codes")
            
            return deleted_count
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error cleaning up expired codes: {str(e)}")
            return 0
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error cleaning up expired codes: {str(e)}")
            return 0
    
    # ==================== UTILITY METHODS ====================
    
    def get_user_count(self) -> int:
        """
        Get the total number of users.
        
        Returns:
            int: Total user count
        """
        try:
            count = self.db.query(User).count()
            logger.debug(f"Total user count: {count}")
            return count
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user count: {str(e)}")
            return 0
    
    def get_users_by_ids(self, user_ids: List[int]) -> List[User]:
        """
        Get multiple users by their IDs.
        
        Args:
            user_ids: List of user IDs
        
        Returns:
            List[User]: List of user objects
        """
        try:
            users = self.db.query(User).filter(User.id.in_(user_ids)).all()
            logger.debug(f"Retrieved {len(users)} users from {len(user_ids)} requested IDs")
            return users
        except SQLAlchemyError as e:
            logger.error(f"Database error getting users by IDs: {str(e)}")
            return []
    
    def email_exists(self, email: str) -> bool:
        """
        Check if an email address is already registered.
        
        Args:
            email: Email address to check
        
        Returns:
            bool: True if email exists, False otherwise
        """
        try:
            exists = self.db.query(User).filter(User.email == email).first() is not None
            logger.debug(f"Email exists check for {email}: {exists}")
            return exists
        except SQLAlchemyError as e:
            logger.error(f"Database error checking email existence for {email}: {str(e)}")
            return False