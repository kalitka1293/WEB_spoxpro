"""
Admin API routes for spoXpro backend.

Provides administrative endpoints for managing products, users, and orders.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from admin.auth import AdminAuthService
from admin.services import AdminProductService, AdminUserService, AdminOrderService
from DTO.store import ProductResponse, CreateProductRequest, UpdateProductRequest
from DTO.user import UserResponse, OrderResponse
from logs.log_store import get_logger

logger = get_logger(__name__)

# Create router
admin_router = APIRouter(prefix="/admin", tags=["admin"])

# Security scheme
security = HTTPBearer()


# Dependency to get admin user ID
async def get_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    admin_auth: AdminAuthService = Depends()
) -> int:
    """Get admin user ID from JWT token."""
    return admin_auth.verify_admin_token(credentials.credentials)


# ==================== PRODUCT MANAGEMENT ====================

@admin_router.get("/products", response_model=List[ProductResponse])
async def get_all_products(
    admin_user_id: int = Depends(get_admin_user),
    admin_product_service: AdminProductService = Depends()
):
    """Get all products for admin management."""
    try:
        products = admin_product_service.get_all_products()
        logger.info(f"Admin {admin_user_id} retrieved {len(products)} products")
        return products
    except Exception as e:
        logger.error(f"Error getting products for admin {admin_user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve products"
        )


@admin_router.post("/products", response_model=ProductResponse)
async def create_product(
    product_data: CreateProductRequest,
    admin_user_id: int = Depends(get_admin_user),
    admin_product_service: AdminProductService = Depends()
):
    """Create a new product."""
    try:
        product = admin_product_service.create_product(product_data.dict())
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create product"
            )
        
        logger.info(f"Admin {admin_user_id} created product: {product.name}")
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product for admin {admin_user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product"
        )


@admin_router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: UpdateProductRequest,
    admin_user_id: int = Depends(get_admin_user),
    admin_product_service: AdminProductService = Depends()
):
    """Update an existing product."""
    try:
        product = admin_product_service.update_product(product_id, product_data.dict())
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        logger.info(f"Admin {admin_user_id} updated product {product_id}")
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product {product_id} for admin {admin_user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product"
        )


@admin_router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    admin_user_id: int = Depends(get_admin_user),
    admin_product_service: AdminProductService = Depends()
):
    """Delete a product."""
    try:
        success = admin_product_service.delete_product(product_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        logger.info(f"Admin {admin_user_id} deleted product {product_id}")
        return {"message": "Product deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product {product_id} for admin {admin_user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
        )


# ==================== USER MANAGEMENT ====================

@admin_router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    admin_user_id: int = Depends(get_admin_user),
    admin_user_service: AdminUserService = Depends()
):
    """Get all users for admin management."""
    try:
        users = admin_user_service.get_all_users()
        logger.info(f"Admin {admin_user_id} retrieved {len(users)} users")
        return users
    except Exception as e:
        logger.error(f"Error getting users for admin {admin_user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@admin_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_details(
    user_id: int,
    admin_user_id: int = Depends(get_admin_user),
    admin_user_service: AdminUserService = Depends()
):
    """Get detailed user information."""
    try:
        user = admin_user_service.get_user_details(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"Admin {admin_user_id} viewed user {user_id} details")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id} for admin {admin_user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


# ==================== ORDER MANAGEMENT ====================

@admin_router.get("/orders", response_model=List[OrderResponse])
async def get_all_orders(
    admin_user_id: int = Depends(get_admin_user),
    admin_order_service: AdminOrderService = Depends()
):
    """Get all orders for admin management."""
    try:
        orders = admin_order_service.get_all_orders()
        logger.info(f"Admin {admin_user_id} retrieved {len(orders)} orders")
        return orders
    except Exception as e:
        logger.error(f"Error getting orders for admin {admin_user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve orders"
        )


@admin_router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: str,
    admin_user_id: int = Depends(get_admin_user),
    admin_order_service: AdminOrderService = Depends()
):
    """Update order status."""
    try:
        success = admin_order_service.update_order_status(order_id, status)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        logger.info(f"Admin {admin_user_id} updated order {order_id} status to {status}")
        return {"message": "Order status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order {order_id} status for admin {admin_user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status"
        )