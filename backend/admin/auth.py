"""
Admin authentication module.

Provides admin-specific authentication and authorization functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional
from fastapi import HTTPException, status
from service.auth_service import AuthService
from logs.log_store import get_logger

logger = get_logger(__name__)


class AdminAuthService:
    """Service for admin authentication and authorization."""
    
    def __init__(self, auth_service: AuthService):
        """
        Initialize admin auth service.
        
        Args:
            auth_service: Regular authentication service
        """
        self.auth_service = auth_service
    
    def verify_admin_token(self, token: str) -> int:
        """
        Verify admin JWT token and return user ID.
        
        Args:
            token: JWT token
            
        Returns:
            int: User ID if valid admin token
            
        Raises:
            HTTPException: If token invalid or user not admin
        """
        try:
            # Validate JWT token
            user_id = self.auth_service.validate_jwt_token(token)
            
            if not user_id:
                logger.warning("Invalid admin token provided")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid admin token"
                )
            
            # Check if user is admin
            if not self.is_admin_user(user_id):
                logger.warning(f"Non-admin user {user_id} attempted admin access")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin privileges required"
                )
            
            logger.info(f"Admin access granted for user {user_id}")
            return user_id
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verifying admin token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )
    
    def is_admin_user(self, user_id: int) -> bool:
        """
        Check if user has admin privileges.
        
        For now, this is a simple implementation.
        In production, this would check a database field or role system.
        
        Args:
            user_id: User ID to check
            
        Returns:
            bool: True if user is admin
        """
        # Simple implementation: user ID 1 is admin
        # In production, check user.is_admin field or roles table
        return user_id == 1
    
    def log_admin_action(self, user_id: int, action: str, details: str = ""):
        """
        Log admin action for audit trail.
        
        Args:
            user_id: Admin user ID
            action: Action performed
            details: Additional details
        """
        logger.info(f"Admin action - User {user_id}: {action} - {details}")