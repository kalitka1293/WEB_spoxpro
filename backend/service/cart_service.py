"""
Cart business logic service for spoXpro backend.

This service provides cart operations with business logic validation,
supporting both authenticated users and guest users via cookies.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, List, Dict, Any
from decimal import Decimal

# Import database services
from db.services.cart_service import CartService as DBCartService

# Import logging
from logs.log_store import get_logger

logger = get_logger(__name__)


class CartService:
    """Business logic service for cart operations."""
    
    def __init__(self, db_cart_service: DBCartService, auth_service):
        """
        Initialize the CartService with database and auth services.
        
        Args:
            db_cart_service: Database cart service instance
            auth_service: Authentication service instance
        """
        self.db_cart_service = db_cart_service
        self.auth_service = auth_service
    
    def add_to_cart(self, user_id: Optional[int], cookie: Optional[str], 
                   product_id: int, size: str, quantity: int):
        """Add an item to the cart with business logic validation."""
        try:
            # Validate authentication
            if not user_id and not cookie:
                raise ValueError("Authentication required: either user login or guest cookie needed")
            
            # Add to cart via database service
            cart_item = self.db_cart_service.add_cart_item(user_id, cookie, product_id, size, quantity)
            
            if not cart_item:
                raise ValueError("Failed to add item to cart")
            
            logger.info(f"Item added to cart: product_id={product_id}, size={size}, quantity={quantity}")
            return cart_item
            
        except Exception as e:
            logger.error(f"Error adding item to cart: {str(e)}")
            raise
    
    def get_cart_contents(self, user_id: Optional[int], cookie: Optional[str]):
        """Get cart contents with business logic validation."""
        try:
            # Validate authentication
            if not user_id and not cookie:
                raise ValueError("Authentication required: either user login or guest cookie needed")
            
            # Get cart contents via database service
            cart_items = self.db_cart_service.get_cart_items(user_id, cookie)
            
            logger.debug(f"Retrieved {len(cart_items)} cart items")
            return cart_items
            
        except Exception as e:
            logger.error(f"Error retrieving cart contents: {str(e)}")
            raise
    
    def update_cart_item(self, item_id: int, quantity: int):
        """Update cart item quantity with validation."""
        try:
            if quantity < 0:
                raise ValueError("Quantity cannot be negative")
            
            cart_item = self.db_cart_service.update_cart_item(item_id, quantity)
            
            if not cart_item:
                raise ValueError(f"Cart item not found: {item_id}")
            
            logger.info(f"Cart item updated: item_id={item_id}, new_quantity={quantity}")
            return cart_item
            
        except Exception as e:
            logger.error(f"Error updating cart item {item_id}: {str(e)}")
            raise
    
    def remove_from_cart(self, item_id: int):
        """Remove an item from the cart."""
        try:
            success = self.db_cart_service.remove_cart_item(item_id)
            
            if not success:
                raise ValueError(f"Cart item not found: {item_id}")
            
            logger.info(f"Item removed from cart: item_id={item_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error removing cart item {item_id}: {str(e)}")
            raise
    
    def clear_cart(self, user_id: Optional[int], cookie: Optional[str]):
        """Clear all items from the cart."""
        try:
            # Validate authentication
            if not user_id and not cookie:
                raise ValueError("Authentication required: either user login or guest cookie needed")
            
            success = self.db_cart_service.clear_cart(user_id, cookie)
            
            if not success:
                raise ValueError("Failed to clear cart")
            
            logger.info(f"Cart cleared for {'user_id=' + str(user_id) if user_id else 'guest'}")
            return success
            
        except Exception as e:
            logger.error(f"Error clearing cart: {str(e)}")
            raise