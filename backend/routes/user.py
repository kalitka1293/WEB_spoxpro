"""
User profile and cart endpoints for spoXpro backend.
Handles user profile management, cart operations, and order history.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Depends, Query, status, Header
from sqlalchemy.orm import Session
from typing import Optional, List
import math

from db.main import get_db_session_context
from db.services.user_service import UserService
from db.services.cart_service import CartService as DBCartService
from db.services.order_service import OrderService
from db.services.product_service import ProductService
from service.auth_service import AuthService
from service.cart_service import CartService as BusinessCartService
from service.order_service import OrderProcessingService as BusinessOrderService
from routes.auth import get_current_user, get_auth_service
from DTO.user import (
    AddToCartRequest, UpdateCartItemRequest, CartItemResponse, CartResponse,
    CreateOrderRequest, OrderResponse, OrderListResponse, UserStatisticsResponse,
    CartValidationResponse, UpdateOrderStatusRequest
)
from DTO.store import ProductSummaryResponse
from DTO.auth import UserProfileResponse, UpdateProfileRequest
from logs.log_store import get_logger

logger = get_logger(__name__)

# Create router for user endpoints
router = APIRouter(prefix="/user", tags=["user"])


def get_cart_service() -> BusinessCartService:
    """Dependency to get CartService instance."""
    with get_db_session_context() as db:
        db_cart_service = DBCartService(db)
        with get_db_session_context() as auth_db:
            user_service = UserService(auth_db)
            auth_service = AuthService(user_service)
            return BusinessCartService(db_cart_service, auth_service)


def get_order_service() -> BusinessOrderService:
    """Dependency to get OrderService instance."""
    with get_db_session_context() as db:
        db_order_service = OrderService(db)
        return BusinessOrderService(db_order_service)


def convert_cart_item_to_response(cart_item, product) -> CartItemResponse:
    """Convert CartItem model to CartItemResponse DTO."""
    product_summary = ProductSummaryResponse(
        id=product.id,
        name=product.name,
        color=product.color,
        gender=product.gender,
        brand=product.brand,
        price=product.price,
        article_number=product.article_number,
        images=product.images or [],
        product_views=product.product_views,
        available_sizes=[size.size for size in product.sizes if size.quantity > 0]
    )
    
    return CartItemResponse(
        id=cart_item.id,
        product=product_summary,
        size=cart_item.size,
        quantity=cart_item.quantity,
        subtotal=product.price * cart_item.quantity,
        added_date=cart_item.created_date
    )


def convert_order_to_response(order) -> OrderResponse:
    """Convert Order model to OrderResponse DTO."""
    order_items = []
    for item in order.items:
        order_items.append({
            "id": item.id,
            "product_name": item.product_name,
            "product_id": item.product_id,
            "size": item.size,
            "quantity": item.quantity,
            "price_at_time": item.price_at_time,
            "subtotal": item.price_at_time * item.quantity
        })
    
    return OrderResponse(
        id=order.id,
        items=order_items,
        total_amount=order.total_amount,
        status=order.status,
        created_date=order.created_date,
        shipping_address=order.shipping_address,
        payment_method=order.payment_method,
        notes=order.notes
    )


# ==================== CART ENDPOINTS ====================

@router.get(
    "/cart",
    response_model=CartResponse,
    summary="Get cart contents",
    description="Retrieve all items in the user's cart. Supports both authenticated users and guest cookies.",
    responses={
        200: {"description": "Cart contents retrieved successfully"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def get_cart(
    guest_cookie: Optional[str] = Header(None, alias="X-Guest-Cookie"),
    current_user = Depends(get_current_user),
    cart_service: BusinessCartService = Depends(get_cart_service)
):
    """Get current user's cart contents."""
    try:
        # Get cart items
        cart_items = cart_service.get_cart_contents(
            user_id=current_user.id if current_user else None,
            cookie=guest_cookie
        )
        
        # Convert to response format
        cart_responses = []
        total = 0
        item_count = 0
        
        with get_db_session_context() as db:
            product_service = ProductService(db)
            
            for cart_item in cart_items:
                product = product_service.get_product_by_id(cart_item.product_id)
                if product:
                    cart_response = convert_cart_item_to_response(cart_item, product)
                    cart_responses.append(cart_response)
                    total += cart_response.subtotal
                    item_count += cart_item.quantity
        
        logger.info(f"Retrieved cart with {len(cart_responses)} items for user: {current_user.id if current_user else 'guest'}")
        
        return CartResponse(
            items=cart_responses,
            total=total,
            item_count=item_count
        )
        
    except Exception as e:
        logger.error(f"Error retrieving cart: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cart contents"
        )


@router.post(
    "/cart/add",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to cart",
    description="Add a product item to the user's cart. Validates inventory availability.",
    responses={
        201: {"description": "Item added to cart successfully"},
        400: {"description": "Invalid request or insufficient inventory"},
        401: {"description": "Authentication required"},
        404: {"description": "Product not found"},
        500: {"description": "Internal server error"}
    }
)
async def add_to_cart(
    request: AddToCartRequest,
    guest_cookie: Optional[str] = Header(None, alias="X-Guest-Cookie"),
    current_user = Depends(get_current_user),
    cart_service: BusinessCartService = Depends(get_cart_service)
):
    """Add an item to the cart."""
    try:
        # Validate product exists and has inventory
        with get_db_session_context() as db:
            product_service = ProductService(db)
            product = product_service.get_product_by_id(request.product_id)
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            
            # Check inventory availability
            if not product_service.check_inventory_availability(
                request.product_id, request.size, request.quantity
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient inventory for requested quantity"
                )
        
        # Add to cart
        cart_item = cart_service.add_to_cart(
            user_id=current_user.id if current_user else None,
            cookie=guest_cookie,
            product_id=request.product_id,
            size=request.size,
            quantity=request.quantity
        )
        
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add item to cart"
            )
        
        # Convert to response format
        cart_response = convert_cart_item_to_response(cart_item, product)
        
        logger.info(f"Item added to cart: product_id={request.product_id}, size={request.size}, quantity={request.quantity}")
        return cart_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding item to cart: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add item to cart"
        )


@router.put(
    "/cart/{item_id}",
    response_model=CartItemResponse,
    summary="Update cart item quantity",
    description="Update the quantity of a specific cart item. Set quantity to 0 to remove the item.",
    responses={
        200: {"description": "Cart item updated successfully"},
        400: {"description": "Invalid quantity or insufficient inventory"},
        401: {"description": "Authentication required"},
        404: {"description": "Cart item not found"},
        500: {"description": "Internal server error"}
    }
)
async def update_cart_item(
    item_id: int,
    request: UpdateCartItemRequest,
    current_user = Depends(get_current_user),
    cart_service: BusinessCartService = Depends(get_cart_service)
):
    """Update cart item quantity."""
    try:
        if request.quantity == 0:
            # Remove item from cart
            success = cart_service.remove_from_cart(item_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cart item not found"
                )
            
            logger.info(f"Item removed from cart: item_id={item_id}")
            return {"message": "Item removed from cart"}
        
        # Update item quantity
        cart_item = cart_service.update_cart_item(item_id, request.quantity)
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found or update failed"
            )
        
        # Get product for response
        with get_db_session_context() as db:
            product_service = ProductService(db)
            product = product_service.get_product_by_id(cart_item.product_id)
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
        
        # Convert to response format
        cart_response = convert_cart_item_to_response(cart_item, product)
        
        logger.info(f"Cart item updated: item_id={item_id}, new_quantity={request.quantity}")
        return cart_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cart item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update cart item"
        )


@router.delete(
    "/cart/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove item from cart",
    description="Remove a specific item from the cart.",
    responses={
        204: {"description": "Item removed successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Cart item not found"},
        500: {"description": "Internal server error"}
    }
)
async def remove_cart_item(
    item_id: int,
    current_user = Depends(get_current_user),
    cart_service: BusinessCartService = Depends(get_cart_service)
):
    """Remove an item from the cart."""
    try:
        success = cart_service.remove_from_cart(item_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found"
            )
        
        logger.info(f"Item removed from cart: item_id={item_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing cart item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove cart item"
        )


@router.delete(
    "/cart",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear cart",
    description="Remove all items from the cart.",
    responses={
        204: {"description": "Cart cleared successfully"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def clear_cart(
    guest_cookie: Optional[str] = Header(None, alias="X-Guest-Cookie"),
    current_user = Depends(get_current_user),
    cart_service: BusinessCartService = Depends(get_cart_service)
):
    """Clear all items from the cart."""
    try:
        success = cart_service.clear_cart(
            user_id=current_user.id if current_user else None,
            cookie=guest_cookie
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to clear cart"
            )
        
        logger.info(f"Cart cleared for user: {current_user.id if current_user else 'guest'}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing cart: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cart"
        )


# ==================== ORDER ENDPOINTS ====================

@router.post(
    "/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order from cart",
    description="Create a new order from the current cart contents. Clears the cart on successful order creation.",
    responses={
        201: {"description": "Order created successfully"},
        400: {"description": "Invalid request or empty cart"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def create_order(
    request: CreateOrderRequest,
    current_user = Depends(get_current_user),
    order_service: BusinessOrderService = Depends(get_order_service)
):
    """Create a new order from cart contents."""
    try:
        # Create order
        order = order_service.create_order(
            user_id=current_user.id,
            order_data={
                "shipping_address": request.shipping_address,
                "payment_method": request.payment_method,
                "notes": request.notes
            }
        )
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create order. Cart may be empty or contain invalid items."
            )
        
        # Convert to response format
        order_response = convert_order_to_response(order)
        
        logger.info(f"Order created: order_id={order.id}, user_id={current_user.id}")
        return order_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )


@router.get(
    "/orders",
    response_model=OrderListResponse,
    summary="Get user orders",
    description="Retrieve the user's order history with pagination.",
    responses={
        200: {"description": "Orders retrieved successfully"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def get_user_orders(
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(10, ge=1, le=50, description="Number of orders per page"),
    current_user = Depends(get_current_user),
    order_service: BusinessOrderService = Depends(get_order_service)
):
    """Get user's order history."""
    try:
        # Calculate pagination
        offset = (page - 1) * page_size
        
        # Get orders
        with get_db_session_context() as db:
            db_order_service = OrderService(db)
            orders = db_order_service.get_user_orders(current_user.id, limit=page_size, offset=offset)
            total_count = db_order_service.get_user_order_count(current_user.id)
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1
        
        # Convert to response format
        order_responses = [convert_order_to_response(order) for order in orders]
        
        logger.info(f"Retrieved {len(orders)} orders for user: {current_user.id}")
        
        return OrderListResponse(
            orders=order_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except Exception as e:
        logger.error(f"Error retrieving user orders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve orders"
        )


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Get specific order",
    description="Retrieve details of a specific order. Users can only access their own orders.",
    responses={
        200: {"description": "Order retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Access denied - not your order"},
        404: {"description": "Order not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_order(
    order_id: int,
    current_user = Depends(get_current_user)
):
    """Get a specific order by ID."""
    try:
        with get_db_session_context() as db:
            db_order_service = OrderService(db)
            order = db_order_service.get_order_by_id(order_id)
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            # Check if user owns this order
            if order.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied - you can only view your own orders"
                )
        
        # Convert to response format
        order_response = convert_order_to_response(order)
        
        logger.info(f"Order retrieved: order_id={order_id}, user_id={current_user.id}")
        return order_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve order"
        )


# ==================== PROFILE ENDPOINTS ====================

@router.get(
    "/profile",
    response_model=UserProfileResponse,
    summary="Get user profile",
    description="Get current user's profile information.",
    responses={
        200: {"description": "Profile retrieved successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "User not found"}
    }
)
async def get_profile(
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current user's profile."""
    try:
        profile = auth_service.get_user_profile(current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        logger.debug(f"Profile retrieved for user: {current_user.email}")
        return UserProfileResponse(**profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.put(
    "/profile",
    response_model=UserProfileResponse,
    summary="Update user profile",
    description="Update current user's profile information.",
    responses={
        200: {"description": "Profile updated successfully"},
        400: {"description": "Invalid input data"},
        401: {"description": "Authentication required"},
        404: {"description": "User not found"}
    }
)
async def update_profile(
    request: UpdateProfileRequest,
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update current user's profile."""
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
                    detail="Current password is required for password change"
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
                    detail="Failed to change password"
                )
        
        # Update other fields if any
        if updates:
            with get_db_session_context() as db:
                user_service = UserService(db)
                updated_user = user_service.update_user(current_user.id, updates)
                if not updated_user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to update profile"
                    )
        
        # Get updated profile
        profile = auth_service.get_user_profile(current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        logger.info(f"Profile updated for user: {current_user.email}")
        return UserProfileResponse(**profile)
        
    except ValueError as e:
        logger.warning(f"Profile update validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )