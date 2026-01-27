"""
Order database service for spoXpro backend.

This service provides comprehensive CRUD operations for orders and order items,
including order creation, status management, and inventory reduction.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from db.models.order import Order, OrderItem, CartItem
from db.models.product import Product, ProductSize
from db.models.user import User
from logs.log_store import get_logger

logger = get_logger(__name__)


class OrderService:
    """Service class for order-related database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the OrderService with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    # ==================== ORDER CRUD OPERATIONS ====================
    
    def create_order(self, user_id: int, order_data: Dict[str, Any]) -> Optional[Order]:
        """
        Create a new order from user's cart items.
        
        Args:
            user_id: User ID
            order_data: Dictionary containing order information:
                - status: str (optional, defaults to "pending")
                - cart_items: List[Dict] (optional, if not provided, uses user's cart)
        
        Returns:
            Order: Created order object or None if creation failed
        """
        try:
            # Get cart items if not provided
            cart_items = order_data.get('cart_items')
            if not cart_items:
                cart_items = self.db.query(CartItem).filter(
                    CartItem.user_id == user_id
                ).options(joinedload(CartItem.product)).all()
            
            if not cart_items:
                logger.error(f"No cart items found for user {user_id}")
                return None
            
            # Validate inventory and calculate total
            total_amount = Decimal('0.00')
            order_items_data = []
            
            for cart_item in cart_items:
                if not cart_item.product:
                    logger.error(f"Product not found for cart item {cart_item.id}")
                    return None
                
                # Check inventory
                product_size = self.db.query(ProductSize).filter(
                    ProductSize.product_id == cart_item.product_id,
                    ProductSize.size == cart_item.size
                ).first()
                
                if not product_size:
                    logger.error(f"Product size not found: product_id={cart_item.product_id}, size={cart_item.size}")
                    return None
                
                if product_size.quantity < cart_item.quantity:
                    logger.error(f"Insufficient inventory: product_id={cart_item.product_id}, size={cart_item.size}, requested={cart_item.quantity}, available={product_size.quantity}")
                    return None
                
                # Calculate item total
                item_total = cart_item.product.price * Decimal(str(cart_item.quantity))
                total_amount += item_total
                
                order_items_data.append({
                    'product_id': cart_item.product_id,
                    'size': cart_item.size,
                    'quantity': cart_item.quantity,
                    'price_at_time': cart_item.product.price
                })
            
            # Create order
            order = Order(
                user_id=user_id,
                total_amount=total_amount,
                status=order_data.get('status', 'pending'),
                created_date=datetime.utcnow()
            )
            
            self.db.add(order)
            self.db.flush()  # Get order ID
            
            # Create order items and reduce inventory
            for item_data in order_items_data:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item_data['product_id'],
                    size=item_data['size'],
                    quantity=item_data['quantity'],
                    price_at_time=item_data['price_at_time']
                )
                self.db.add(order_item)
                
                # Reduce inventory
                product_size = self.db.query(ProductSize).filter(
                    ProductSize.product_id == item_data['product_id'],
                    ProductSize.size == item_data['size']
                ).first()
                
                if product_size:
                    product_size.quantity -= item_data['quantity']
            
            # Clear user's cart
            self.db.query(CartItem).filter(CartItem.user_id == user_id).delete()
            
            self.db.commit()
            self.db.refresh(order)
            
            logger.info(f"Order created successfully: order_id={order.id}, user_id={user_id}, total={total_amount}")
            return order
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating order for user {user_id}: {str(e)}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating order for user {user_id}: {str(e)}")
            return None
    
    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """
        Retrieve an order by its ID.
        
        Args:
            order_id: Order ID
        
        Returns:
            Order: Order object with items or None if not found
        """
        try:
            order = self.db.query(Order).options(
                joinedload(Order.items).joinedload(OrderItem.product),
                joinedload(Order.user)
            ).filter(Order.id == order_id).first()
            
            if order:
                logger.debug(f"Order found with ID: {order_id}")
            else:
                logger.debug(f"Order not found with ID: {order_id}")
            
            return order
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving order {order_id}: {str(e)}")
            return None
    
    def get_user_orders(self, user_id: int, limit: Optional[int] = None, 
                       offset: Optional[int] = None) -> List[Order]:
        """
        Retrieve all orders for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of orders to return
            offset: Number of orders to skip
        
        Returns:
            List[Order]: List of orders with items
        """
        try:
            query = self.db.query(Order).options(
                joinedload(Order.items).joinedload(OrderItem.product)
            ).filter(Order.user_id == user_id).order_by(desc(Order.created_date))
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            orders = query.all()
            
            logger.debug(f"Retrieved {len(orders)} orders for user {user_id}")
            return orders
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving orders for user {user_id}: {str(e)}")
            return []
    
    def update_order_status(self, order_id: int, status: str) -> Optional[Order]:
        """
        Update the status of an order.
        
        Args:
            order_id: Order ID
            status: New status (pending, confirmed, shipped, delivered, cancelled)
        
        Returns:
            Order: Updated order object or None if update failed
        """
        try:
            order = self.get_order_by_id(order_id)
            if not order:
                logger.error(f"Order not found with ID: {order_id}")
                return None
            
            # Validate status
            valid_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
            if status not in valid_statuses:
                logger.error(f"Invalid order status: {status}")
                return None
            
            order.status = status
            self.db.commit()
            self.db.refresh(order)
            
            logger.info(f"Order status updated: order_id={order_id}, new_status={status}")
            return order
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating order status {order_id}: {str(e)}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error updating order status {order_id}: {str(e)}")
            return None
    
    def cancel_order(self, order_id: int) -> bool:
        """
        Cancel an order and restore inventory.
        
        Args:
            order_id: Order ID
        
        Returns:
            bool: True if cancellation was successful, False otherwise
        """
        try:
            order = self.get_order_by_id(order_id)
            if not order:
                logger.error(f"Order not found with ID: {order_id}")
                return False
            
            # Only allow cancellation of pending or confirmed orders
            if order.status not in ["pending", "confirmed"]:
                logger.error(f"Cannot cancel order with status: {order.status}")
                return False
            
            # Restore inventory
            for order_item in order.items:
                product_size = self.db.query(ProductSize).filter(
                    ProductSize.product_id == order_item.product_id,
                    ProductSize.size == order_item.size
                ).first()
                
                if product_size:
                    product_size.quantity += order_item.quantity
            
            # Update order status
            order.status = "cancelled"
            self.db.commit()
            
            logger.info(f"Order cancelled successfully: order_id={order_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error cancelling order {order_id}: {str(e)}")
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error cancelling order {order_id}: {str(e)}")
            return False
    
    # ==================== ORDER ITEM OPERATIONS ====================
    
    def create_order_items(self, order_id: int, items_data: List[Dict[str, Any]]) -> List[OrderItem]:
        """
        Create order items for an existing order.
        
        Args:
            order_id: Order ID
            items_data: List of dictionaries containing item information
        
        Returns:
            List[OrderItem]: Created order items
        """
        try:
            order_items = []
            
            for item_data in items_data:
                order_item = OrderItem(
                    order_id=order_id,
                    product_id=item_data['product_id'],
                    size=item_data['size'],
                    quantity=item_data['quantity'],
                    price_at_time=item_data['price_at_time']
                )
                
                self.db.add(order_item)
                order_items.append(order_item)
            
            self.db.commit()
            
            for item in order_items:
                self.db.refresh(item)
            
            logger.info(f"Created {len(order_items)} order items for order {order_id}")
            return order_items
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating order items for order {order_id}: {str(e)}")
            return []
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating order items for order {order_id}: {str(e)}")
            return []
    
    def get_order_item_by_id(self, item_id: int) -> Optional[OrderItem]:
        """
        Get an order item by its ID.
        
        Args:
            item_id: Order item ID
        
        Returns:
            OrderItem: Order item or None if not found
        """
        try:
            order_item = self.db.query(OrderItem).options(
                joinedload(OrderItem.product),
                joinedload(OrderItem.order)
            ).filter(OrderItem.id == item_id).first()
            
            if order_item:
                logger.debug(f"Order item found with ID: {item_id}")
            else:
                logger.debug(f"Order item not found with ID: {item_id}")
            
            return order_item
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving order item {item_id}: {str(e)}")
            return None
    
    # ==================== ORDER STATISTICS ====================
    
    def get_order_count_by_user(self, user_id: int) -> int:
        """
        Get the total number of orders for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            int: Total order count
        """
        try:
            count = self.db.query(Order).filter(Order.user_id == user_id).count()
            logger.debug(f"Order count for user {user_id}: {count}")
            return count
        except SQLAlchemyError as e:
            logger.error(f"Database error getting order count for user {user_id}: {str(e)}")
            return 0
    
    def get_order_total_by_user(self, user_id: int) -> Decimal:
        """
        Get the total amount spent by a user across all orders.
        
        Args:
            user_id: User ID
        
        Returns:
            Decimal: Total amount spent
        """
        try:
            from sqlalchemy import func
            
            result = self.db.query(func.sum(Order.total_amount)).filter(
                Order.user_id == user_id,
                Order.status != "cancelled"
            ).scalar()
            
            total = result if result else Decimal('0.00')
            logger.debug(f"Total spent by user {user_id}: {total}")
            return total
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting order total for user {user_id}: {str(e)}")
            return Decimal('0.00')
    
    def get_orders_by_status(self, status: str, limit: Optional[int] = None) -> List[Order]:
        """
        Get orders by status.
        
        Args:
            status: Order status
            limit: Maximum number of orders to return
        
        Returns:
            List[Order]: List of orders with the specified status
        """
        try:
            query = self.db.query(Order).options(
                joinedload(Order.items).joinedload(OrderItem.product),
                joinedload(Order.user)
            ).filter(Order.status == status).order_by(desc(Order.created_date))
            
            if limit:
                query = query.limit(limit)
            
            orders = query.all()
            
            logger.debug(f"Retrieved {len(orders)} orders with status: {status}")
            return orders
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving orders by status {status}: {str(e)}")
            return []
    
    # ==================== INVENTORY MANAGEMENT ====================
    
    def validate_order_inventory(self, cart_items: List[CartItem]) -> Dict[str, Any]:
        """
        Validate that all cart items have sufficient inventory for order creation.
        
        Args:
            cart_items: List of cart items to validate
        
        Returns:
            Dict: Validation result with 'valid' boolean and 'issues' list
        """
        try:
            issues = []
            
            for cart_item in cart_items:
                # Check if product still exists
                if not cart_item.product:
                    issues.append({
                        'cart_item_id': cart_item.id,
                        'product_id': cart_item.product_id,
                        'issue': 'product_not_found',
                        'message': f'Product no longer exists'
                    })
                    continue
                
                # Check inventory for the specific size
                product_size = self.db.query(ProductSize).filter(
                    ProductSize.product_id == cart_item.product_id,
                    ProductSize.size == cart_item.size
                ).first()
                
                if not product_size:
                    issues.append({
                        'cart_item_id': cart_item.id,
                        'product_id': cart_item.product_id,
                        'size': cart_item.size,
                        'issue': 'size_not_available',
                        'message': f'Size {cart_item.size} no longer available'
                    })
                elif product_size.quantity < cart_item.quantity:
                    issues.append({
                        'cart_item_id': cart_item.id,
                        'product_id': cart_item.product_id,
                        'size': cart_item.size,
                        'issue': 'insufficient_inventory',
                        'message': f'Only {product_size.quantity} available, but {cart_item.quantity} requested',
                        'available_quantity': product_size.quantity,
                        'requested_quantity': cart_item.quantity
                    })
            
            result = {
                'valid': len(issues) == 0,
                'issues': issues
            }
            
            logger.debug(f"Order inventory validation result: {len(issues)} issues found")
            return result
            
        except Exception as e:
            logger.error(f"Error validating order inventory: {str(e)}")
            return {'valid': False, 'issues': [{'issue': 'validation_error', 'message': str(e)}]}
    
    # ==================== UTILITY METHODS ====================
    
    def get_recent_orders(self, limit: int = 10) -> List[Order]:
        """
        Get the most recent orders across all users.
        
        Args:
            limit: Maximum number of orders to return
        
        Returns:
            List[Order]: List of recent orders
        """
        try:
            orders = self.db.query(Order).options(
                joinedload(Order.user),
                joinedload(Order.items).joinedload(OrderItem.product)
            ).order_by(desc(Order.created_date)).limit(limit).all()
            
            logger.debug(f"Retrieved {len(orders)} recent orders")
            return orders
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving recent orders: {str(e)}")
            return []
    
    def get_order_statistics(self) -> Dict[str, Any]:
        """
        Get overall order statistics.
        
        Returns:
            Dict: Statistics including total orders, total revenue, etc.
        """
        try:
            from sqlalchemy import func
            
            # Total orders
            total_orders = self.db.query(Order).count()
            
            # Total revenue (excluding cancelled orders)
            total_revenue = self.db.query(func.sum(Order.total_amount)).filter(
                Order.status != "cancelled"
            ).scalar() or Decimal('0.00')
            
            # Orders by status
            status_counts = {}
            for status in ["pending", "confirmed", "shipped", "delivered", "cancelled"]:
                count = self.db.query(Order).filter(Order.status == status).count()
                status_counts[status] = count
            
            # Average order value
            avg_order_value = Decimal('0.00')
            if total_orders > 0:
                avg_order_value = total_revenue / Decimal(str(total_orders))
            
            statistics = {
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'average_order_value': avg_order_value,
                'orders_by_status': status_counts
            }
            
            logger.debug(f"Order statistics calculated: {statistics}")
            return statistics
            
        except SQLAlchemyError as e:
            logger.error(f"Database error calculating order statistics: {str(e)}")
            return {
                'total_orders': 0,
                'total_revenue': Decimal('0.00'),
                'average_order_value': Decimal('0.00'),
                'orders_by_status': {}
            }