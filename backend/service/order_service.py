"""
Order Processing Business Logic Service

This service handles order creation, validation, inventory management,
and order completion workflows for the spoXpro e-commerce platform.

Requirements: 5.1, 5.2, 5.3, 5.6
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
import logging

from db.services.order_service import OrderService as OrderDBService
from db.services.cart_service import CartService as DBCartService
from db.services.product_service import ProductService
from db.models.order import Order, OrderItem
from db.models.order import CartItem
from DTO.user import CreateOrderRequest, OrderResponse, OrderItemResponse
from logs.log_store import get_logger

logger = get_logger(__name__)


class OrderProcessingService:
    """
    Business logic service for order processing operations.
    
    Handles order creation with inventory management, order completion workflow
    with cart clearing, and order validation and history management.
    """

    def __init__(
        self, 
        order_db_service: OrderDBService,
        cart_service: DBCartService,
        product_service: ProductService
    ):
        """
        Initialize the order processing service.
        
        Args:
            order_db_service: Database service for order operations
            cart_service: Database service for cart operations
            product_service: Database service for product operations
        """
        self.order_db_service = order_db_service
        self.cart_service = cart_service
        self.product_service = product_service

    def create_order(
        self, 
        user_id: int, 
        order_request: CreateOrderRequest
    ) -> OrderResponse:
        """
        Create a new order from user's cart contents.
        
        This method:
        1. Validates cart contents and inventory availability
        2. Creates order record with cart contents and user information
        3. Reduces product inventory quantities for purchased items
        4. Clears the user's cart upon successful order creation
        5. Returns complete order details
        
        Args:
            user_id: ID of the user placing the order
            order_request: Order creation request with shipping and payment info
            
        Returns:
            OrderResponse: Complete order details
            
        Raises:
            ValueError: If cart is empty or inventory insufficient
            Exception: If order creation fails
        """
        try:
            logger.info(f"Creating order for user {user_id}")
            
            # Get user's cart items
            cart_items = self.cart_service.get_cart_items(user_id=user_id, cookie=None)
            
            if not cart_items:
                raise ValueError("Cannot create order: cart is empty")
            
            # Validate inventory availability for all items
            self._validate_cart_inventory(cart_items)
            
            # Calculate total amount
            total_amount = self._calculate_order_total(cart_items)
            
            # Create order record
            order_data = {
                'user_id': user_id,
                'total_amount': total_amount,
                'status': 'pending',
                'shipping_address': order_request.shipping_address,
                'payment_method': order_request.payment_method
            }
            
            order = self.order_db_service.create_order(user_id, order_data)
            
            # Create order items and reduce inventory
            order_items = []
            for cart_item in cart_items:
                # Get current product price
                product = self.product_service.get_product_by_id(cart_item.product_id)
                
                # Create order item
                order_item_data = {
                    'product_id': cart_item.product_id,
                    'size': cart_item.size,
                    'quantity': cart_item.quantity,
                    'price_at_time': product.price
                }
                
                order_item = self.order_db_service.create_order_items(order.id, [order_item_data])[0]
                order_items.append(order_item)
                
                # Reduce inventory
                success = self.product_service.update_product_inventory(
                    product_id=cart_item.product_id,
                    size=cart_item.size,
                    quantity_change=-cart_item.quantity
                )
                
                if not success:
                    # Log the inventory update failure but continue
                    logger.warning(f"Failed to update inventory for product {cart_item.product_id}, size {cart_item.size}")
                    # In a real system, you might want to implement proper rollback
                    # For now, we'll let the order proceed but log the issue
            
            # Clear user's cart after successful order creation
            self.cart_service.clear_cart(user_id=user_id, cookie=None)
            
            # Update order status to confirmed
            self.order_db_service.update_order_status(order.id, 'confirmed')
            
            logger.info(f"Order {order.id} created successfully for user {user_id}")
            
            # Return order response
            return self._build_order_response(order, order_items)
            
        except Exception as e:
            logger.error(f"Failed to create order for user {user_id}: {str(e)}")
            raise

    def get_user_orders(self, user_id: int) -> List[OrderResponse]:
        """
        Get all orders for a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List[OrderResponse]: List of user's orders with complete details
        """
        try:
            logger.info(f"Retrieving orders for user {user_id}")
            
            orders = self.order_db_service.get_user_orders(user_id)
            order_responses = []
            
            for order in orders:
                order_items = order.items  # Items are already loaded via joinedload
                order_response = self._build_order_response(order, order_items)
                order_responses.append(order_response)
            
            logger.info(f"Retrieved {len(order_responses)} orders for user {user_id}")
            return order_responses
            
        except Exception as e:
            logger.error(f"Failed to retrieve orders for user {user_id}: {str(e)}")
            raise

    def get_order_by_id(self, order_id: int, user_id: int) -> Optional[OrderResponse]:
        """
        Get a specific order by ID, ensuring it belongs to the user.
        
        Args:
            order_id: ID of the order
            user_id: ID of the user (for authorization)
            
        Returns:
            OrderResponse: Order details if found and authorized, None otherwise
        """
        try:
            order = self.order_db_service.get_order_by_id(order_id)
            
            if not order or order.user_id != user_id:
                return None
            
            order_items = self.order_db_service.get_order_items(order.id)
            return self._build_order_response(order, order_items)
            
        except Exception as e:
            logger.error(f"Failed to retrieve order {order_id}: {str(e)}")
            raise

    def update_order_status(self, order_id: int, status: str, user_id: int = None) -> bool:
        """
        Update order status.
        
        Args:
            order_id: ID of the order
            status: New status for the order
            user_id: Optional user ID for authorization (admin can update any order)
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # If user_id provided, verify order belongs to user
            if user_id:
                order = self.order_db_service.get_order_by_id(order_id)
                if not order or order.user_id != user_id:
                    return False
            
            updated_order = self.order_db_service.update_order_status(order_id, status)
            
            if updated_order:
                logger.info(f"Order {order_id} status updated to {status}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update order {order_id} status: {str(e)}")
            return False

    def cancel_order(self, order_id: int, user_id: int) -> bool:
        """
        Cancel an order and restore inventory.
        
        Args:
            order_id: ID of the order to cancel
            user_id: ID of the user (for authorization)
            
        Returns:
            bool: True if cancellation successful, False otherwise
        """
        try:
            # Get order and verify ownership
            order = self.order_db_service.get_order_by_id(order_id)
            
            if not order or order.user_id != user_id:
                logger.warning(f"Unauthorized cancellation attempt for order {order_id} by user {user_id}")
                return False
            
            # Only allow cancellation of pending/confirmed orders
            if order.status not in ['pending', 'confirmed']:
                logger.warning(f"Cannot cancel order {order_id} with status {order.status}")
                return False
            
            # Get order items to restore inventory
            order_items = self.order_db_service.get_order_items(order.id)
            
            # Restore inventory for each item
            for item in order_items:
                success = self.product_service.update_inventory(
                    product_id=item.product_id,
                    size=item.size,
                    quantity_change=item.quantity  # Add back to inventory
                )
                
                if not success:
                    logger.error(f"Failed to restore inventory for product {item.product_id}")
                    # Continue with other items even if one fails
            
            # Update order status to cancelled
            self.order_db_service.update_order_status(order_id, 'cancelled')
            
            logger.info(f"Order {order_id} cancelled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            return False

    def _validate_cart_inventory(self, cart_items: List[CartItem]) -> None:
        """
        Validate that all cart items have sufficient inventory.
        
        Args:
            cart_items: List of cart items to validate
            
        Raises:
            ValueError: If any item has insufficient inventory
        """
        for cart_item in cart_items:
            available_inventory = self.product_service.get_product_inventory(
                cart_item.product_id, 
                cart_item.size
            )
            
            if available_inventory < cart_item.quantity:
                product = self.product_service.get_product_by_id(cart_item.product_id)
                raise ValueError(
                    f"Insufficient inventory for {product.name} (size {cart_item.size}). "
                    f"Requested: {cart_item.quantity}, Available: {available_inventory}"
                )

    def _calculate_order_total(self, cart_items: List[CartItem]) -> Decimal:
        """
        Calculate total amount for cart items.
        
        Args:
            cart_items: List of cart items
            
        Returns:
            Decimal: Total amount for the order
        """
        total = Decimal('0.00')
        
        for cart_item in cart_items:
            product = self.product_service.get_product_by_id(cart_item.product_id)
            item_total = product.price * cart_item.quantity
            total += item_total
        
        return total

    def _build_order_response(self, order: Order, order_items: List[OrderItem]) -> OrderResponse:
        """
        Build OrderResponse from order and order items.
        
        Args:
            order: Order database model
            order_items: List of order item database models
            
        Returns:
            OrderResponse: Complete order response DTO
        """
        # Build order item responses
        item_responses = []
        for item in order_items:
            product = self.product_service.get_product_by_id(item.product_id)
            
            item_response = OrderItemResponse(
                id=item.id,
                product_name=product.name,
                product_id=item.product_id,
                size=item.size,
                quantity=item.quantity,
                price_at_time=item.price_at_time,
                subtotal=item.price_at_time * item.quantity
            )
            item_responses.append(item_response)
        
        # Build order response
        return OrderResponse(
            id=order.id,
            items=item_responses,
            total_amount=order.total_amount,
            status=order.status,
            created_date=order.created_date
        )

    def process_payment(self, order_id: int, payment_info: Dict[str, Any]) -> bool:
        """
        Process payment for an order.
        
        Note: This is a placeholder for payment processing integration.
        In a real implementation, this would integrate with payment providers.
        
        Args:
            order_id: ID of the order to process payment for
            payment_info: Payment information dictionary
            
        Returns:
            bool: True if payment successful, False otherwise
        """
        try:
            # Placeholder payment processing logic
            # In real implementation, integrate with Stripe, PayPal, etc.
            
            logger.info(f"Processing payment for order {order_id}")
            
            # Simulate payment processing
            # For now, assume all payments succeed
            payment_successful = True
            
            if payment_successful:
                # Update order status to paid
                self.order_db_service.update_order_status(order_id, 'paid')
                logger.info(f"Payment processed successfully for order {order_id}")
                return True
            else:
                logger.warning(f"Payment failed for order {order_id}")
                return False
                
        except Exception as e:
            logger.error(f"Payment processing failed for order {order_id}: {str(e)}")
            return False

    def get_order_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get order statistics for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict[str, Any]: Order statistics including total orders, total spent, etc.
        """
        try:
            orders = self.order_db_service.get_user_orders(user_id)
            
            total_orders = len(orders)
            total_spent = sum(order.total_amount for order in orders)
            
            # Count orders by status
            status_counts = {}
            for order in orders:
                status_counts[order.status] = status_counts.get(order.status, 0) + 1
            
            return {
                'total_orders': total_orders,
                'total_spent': total_spent,
                'status_breakdown': status_counts,
                'average_order_value': total_spent / total_orders if total_orders > 0 else Decimal('0.00')
            }
            
        except Exception as e:
            logger.error(f"Failed to get order statistics for user {user_id}: {str(e)}")
            return {
                'total_orders': 0,
                'total_spent': Decimal('0.00'),
                'status_breakdown': {},
                'average_order_value': Decimal('0.00')
            }