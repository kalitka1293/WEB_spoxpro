"""
Cart database service for spoXpro backend.

This service provides comprehensive CRUD operations for cart items,
supporting both authenticated users and guest users via cookies.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from db.models.order import CartItem
from db.models.product import Product, ProductSize
from db.models.user import User
from logs.log_store import get_logger

logger = get_logger(__name__)


class CartService:
    """Service class for cart-related database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the CartService with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    # ==================== CART ITEM CRUD OPERATIONS ====================
    
    def add_cart_item(self, user_id: Optional[int], cookie: Optional[str], 
                     product_id: int, size: str, quantity: int) -> Optional[CartItem]:
        """
        Add an item to the cart for a user or guest.
        
        Args:
            user_id: User ID (for authenticated users)
            cookie: Cookie value (for guest users)
            product_id: ID of the product to add
            size: Size of the product
            quantity: Quantity to add
        
        Returns:
            CartItem: Created or updated cart item, or None if failed
        """
        try:
            # Validate that either user_id or cookie is provided
            if not user_id and not cookie:
                logger.error("Either user_id or cookie must be provided")
                return None
            
            # Check if product and size exist and have sufficient inventory
            product_size = self.db.query(ProductSize).filter(
                ProductSize.product_id == product_id,
                ProductSize.size == size
            ).first()
            
            if not product_size:
                logger.error(f"Product size not found: product_id={product_id}, size={size}")
                return None
            
            if product_size.quantity < quantity:
                logger.error(f"Insufficient inventory: requested={quantity}, available={product_size.quantity}")
                return None
            
            # Check if item already exists in cart
            existing_item = self.db.query(CartItem).filter(
                CartItem.product_id == product_id,
                CartItem.size == size
            )
            
            if user_id:
                existing_item = existing_item.filter(CartItem.user_id == user_id)
            else:
                existing_item = existing_item.filter(CartItem.cookie == cookie)
            
            existing_item = existing_item.first()
            
            if existing_item:
                # Update existing item quantity
                new_quantity = existing_item.quantity + quantity
                if product_size.quantity < new_quantity:
                    logger.error(f"Insufficient inventory for update: requested={new_quantity}, available={product_size.quantity}")
                    return None
                
                existing_item.quantity = new_quantity
                self.db.commit()
                self.db.refresh(existing_item)
                
                logger.info(f"Cart item updated: product_id={product_id}, size={size}, new_quantity={new_quantity}")
                return existing_item
            else:
                # Create new cart item
                cart_item = CartItem(
                    user_id=user_id,
                    cookie=cookie,
                    product_id=product_id,
                    size=size,
                    quantity=quantity
                )
                
                self.db.add(cart_item)
                self.db.commit()
                self.db.refresh(cart_item)
                
                logger.info(f"Cart item added: product_id={product_id}, size={size}, quantity={quantity}")
                return cart_item
                
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error adding cart item: {str(e)}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error adding cart item: {str(e)}")
            return None
    
    def get_cart_items(self, user_id: Optional[int], cookie: Optional[str]) -> List[CartItem]:
        """
        Get all cart items for a user or guest.
        
        Args:
            user_id: User ID (for authenticated users)
            cookie: Cookie value (for guest users)
        
        Returns:
            List[CartItem]: List of cart items with product information
        """
        try:
            # Validate that either user_id or cookie is provided
            if not user_id and not cookie:
                logger.error("Either user_id or cookie must be provided")
                return []
            
            query = self.db.query(CartItem).options(
                joinedload(CartItem.product).joinedload(Product.sizes)
            )
            
            if user_id:
                query = query.filter(CartItem.user_id == user_id)
            else:
                query = query.filter(CartItem.cookie == cookie)
            
            cart_items = query.all()
            
            logger.debug(f"Retrieved {len(cart_items)} cart items for {'user_id=' + str(user_id) if user_id else 'cookie=' + cookie[:8] + '...'}")
            return cart_items
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving cart items: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving cart items: {str(e)}")
            return []
    
    def update_cart_item(self, item_id: int, quantity: int) -> Optional[CartItem]:
        """
        Update the quantity of a cart item.
        
        Args:
            item_id: Cart item ID
            quantity: New quantity
        
        Returns:
            CartItem: Updated cart item or None if failed
        """
        try:
            cart_item = self.db.query(CartItem).filter(CartItem.id == item_id).first()
            if not cart_item:
                logger.error(f"Cart item not found with ID: {item_id}")
                return None
            
            # Check inventory availability
            product_size = self.db.query(ProductSize).filter(
                ProductSize.product_id == cart_item.product_id,
                ProductSize.size == cart_item.size
            ).first()
            
            if not product_size:
                logger.error(f"Product size not found for cart item: {item_id}")
                return None
            
            if product_size.quantity < quantity:
                logger.error(f"Insufficient inventory: requested={quantity}, available={product_size.quantity}")
                return None
            
            cart_item.quantity = quantity
            self.db.commit()
            self.db.refresh(cart_item)
            
            logger.info(f"Cart item updated: item_id={item_id}, new_quantity={quantity}")
            return cart_item
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating cart item {item_id}: {str(e)}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error updating cart item {item_id}: {str(e)}")
            return None
    
    def remove_cart_item(self, item_id: int) -> bool:
        """
        Remove a cart item.
        
        Args:
            item_id: Cart item ID
        
        Returns:
            bool: True if removal was successful, False otherwise
        """
        try:
            cart_item = self.db.query(CartItem).filter(CartItem.id == item_id).first()
            if not cart_item:
                logger.error(f"Cart item not found with ID: {item_id}")
                return False
            
            self.db.delete(cart_item)
            self.db.commit()
            
            logger.info(f"Cart item removed: item_id={item_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error removing cart item {item_id}: {str(e)}")
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error removing cart item {item_id}: {str(e)}")
            return False
    
    def clear_cart(self, user_id: Optional[int], cookie: Optional[str]) -> bool:
        """
        Clear all cart items for a user or guest.
        
        Args:
            user_id: User ID (for authenticated users)
            cookie: Cookie value (for guest users)
        
        Returns:
            bool: True if clearing was successful, False otherwise
        """
        try:
            # Validate that either user_id or cookie is provided
            if not user_id and not cookie:
                logger.error("Either user_id or cookie must be provided")
                return False
            
            query = self.db.query(CartItem)
            
            if user_id:
                query = query.filter(CartItem.user_id == user_id)
            else:
                query = query.filter(CartItem.cookie == cookie)
            
            deleted_count = query.delete()
            self.db.commit()
            
            logger.info(f"Cart cleared: {deleted_count} items removed for {'user_id=' + str(user_id) if user_id else 'cookie=' + cookie[:8] + '...'}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error clearing cart: {str(e)}")
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error clearing cart: {str(e)}")
            return False
    
    # ==================== CART CALCULATIONS ====================
    
    def calculate_cart_total(self, user_id: Optional[int], cookie: Optional[str]) -> Decimal:
        """
        Calculate the total value of items in the cart.
        
        Args:
            user_id: User ID (for authenticated users)
            cookie: Cookie value (for guest users)
        
        Returns:
            Decimal: Total cart value
        """
        try:
            cart_items = self.get_cart_items(user_id, cookie)
            total = Decimal('0.00')
            
            for item in cart_items:
                if item.product:
                    item_total = item.product.price * Decimal(str(item.quantity))
                    total += item_total
            
            logger.debug(f"Cart total calculated: {total}")
            return total
            
        except Exception as e:
            logger.error(f"Error calculating cart total: {str(e)}")
            return Decimal('0.00')
    
    def get_cart_item_count(self, user_id: Optional[int], cookie: Optional[str]) -> int:
        """
        Get the total number of items in the cart.
        
        Args:
            user_id: User ID (for authenticated users)
            cookie: Cookie value (for guest users)
        
        Returns:
            int: Total item count
        """
        try:
            cart_items = self.get_cart_items(user_id, cookie)
            total_count = sum(item.quantity for item in cart_items)
            
            logger.debug(f"Cart item count: {total_count}")
            return total_count
            
        except Exception as e:
            logger.error(f"Error calculating cart item count: {str(e)}")
            return 0
    
    # ==================== CART VALIDATION ====================
    
    def validate_cart_inventory(self, user_id: Optional[int], cookie: Optional[str]) -> Dict[str, Any]:
        """
        Validate that all cart items have sufficient inventory.
        
        Args:
            user_id: User ID (for authenticated users)
            cookie: Cookie value (for guest users)
        
        Returns:
            Dict: Validation result with 'valid' boolean and 'issues' list
        """
        try:
            cart_items = self.get_cart_items(user_id, cookie)
            issues = []
            
            for item in cart_items:
                # Check if product still exists
                if not item.product:
                    issues.append({
                        'item_id': item.id,
                        'issue': 'product_not_found',
                        'message': f'Product no longer exists'
                    })
                    continue
                
                # Check inventory for the specific size
                product_size = self.db.query(ProductSize).filter(
                    ProductSize.product_id == item.product_id,
                    ProductSize.size == item.size
                ).first()
                
                if not product_size:
                    issues.append({
                        'item_id': item.id,
                        'issue': 'size_not_available',
                        'message': f'Size {item.size} no longer available'
                    })
                elif product_size.quantity < item.quantity:
                    issues.append({
                        'item_id': item.id,
                        'issue': 'insufficient_inventory',
                        'message': f'Only {product_size.quantity} available, but {item.quantity} requested',
                        'available_quantity': product_size.quantity,
                        'requested_quantity': item.quantity
                    })
            
            result = {
                'valid': len(issues) == 0,
                'issues': issues
            }
            
            logger.debug(f"Cart validation result: {len(issues)} issues found")
            return result
            
        except Exception as e:
            logger.error(f"Error validating cart inventory: {str(e)}")
            return {'valid': False, 'issues': [{'issue': 'validation_error', 'message': str(e)}]}
    
    # ==================== CART MIGRATION ====================
    
    def migrate_guest_cart_to_user(self, cookie: str, user_id: int) -> bool:
        """
        Migrate cart items from guest cookie to authenticated user.
        
        Args:
            cookie: Guest cookie value
            user_id: User ID to migrate to
        
        Returns:
            bool: True if migration was successful, False otherwise
        """
        try:
            # Get guest cart items
            guest_items = self.db.query(CartItem).filter(CartItem.cookie == cookie).all()
            
            if not guest_items:
                logger.debug(f"No guest cart items to migrate for cookie: {cookie[:8]}...")
                return True
            
            # Get existing user cart items
            user_items = self.db.query(CartItem).filter(CartItem.user_id == user_id).all()
            user_items_dict = {(item.product_id, item.size): item for item in user_items}
            
            migrated_count = 0
            
            for guest_item in guest_items:
                key = (guest_item.product_id, guest_item.size)
                
                if key in user_items_dict:
                    # Merge quantities
                    user_item = user_items_dict[key]
                    user_item.quantity += guest_item.quantity
                    self.db.delete(guest_item)
                else:
                    # Transfer item to user
                    guest_item.user_id = user_id
                    guest_item.cookie = None
                
                migrated_count += 1
            
            self.db.commit()
            
            logger.info(f"Cart migration completed: {migrated_count} items migrated from cookie to user_id={user_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error migrating cart: {str(e)}")
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error migrating cart: {str(e)}")
            return False
    
    # ==================== UTILITY METHODS ====================
    
    def get_cart_item_by_id(self, item_id: int) -> Optional[CartItem]:
        """
        Get a cart item by its ID.
        
        Args:
            item_id: Cart item ID
        
        Returns:
            CartItem: Cart item or None if not found
        """
        try:
            cart_item = self.db.query(CartItem).options(
                joinedload(CartItem.product)
            ).filter(CartItem.id == item_id).first()
            
            if cart_item:
                logger.debug(f"Cart item found with ID: {item_id}")
            else:
                logger.debug(f"Cart item not found with ID: {item_id}")
            
            return cart_item
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving cart item {item_id}: {str(e)}")
            return None
    
    def cleanup_expired_guest_carts(self, days_old: int = 30) -> int:
        """
        Clean up old guest cart items.
        
        Args:
            days_old: Number of days after which to consider carts expired
        
        Returns:
            int: Number of cart items deleted
        """
        try:
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            deleted_count = self.db.query(CartItem).filter(
                CartItem.cookie.isnot(None),
                CartItem.added_date < cutoff_date
            ).delete()
            
            self.db.commit()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired guest cart items")
            
            return deleted_count
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error cleaning up expired carts: {str(e)}")
            return 0
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error cleaning up expired carts: {str(e)}")
            return 0