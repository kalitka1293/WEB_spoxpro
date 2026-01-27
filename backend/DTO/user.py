"""
User and cart-related Pydantic DTO models for spoXpro backend.

These models define the request and response structures for user endpoints,
including cart operations, order management, and user profile data.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from .store import SizeEnum, ProductSummaryResponse


class AddToCartRequest(BaseModel):
    """Request model for adding items to cart."""
    
    product_id: int = Field(..., gt=0, description="Product ID to add to cart")
    size: SizeEnum = Field(..., description="Product size")
    quantity: int = Field(..., gt=0, le=99, description="Quantity to add (1-99)")
    
    class Config:
        schema_extra = {
            "example": {
                "product_id": 1,
                "size": "M",
                "quantity": 2
            }
        }


class UpdateCartItemRequest(BaseModel):
    """Request model for updating cart item quantity."""
    
    quantity: int = Field(..., ge=0, le=99, description="New quantity (0 to remove item)")
    
    class Config:
        schema_extra = {
            "example": {
                "quantity": 3
            }
        }


class CartItemResponse(BaseModel):
    """Response model for cart item information."""
    
    id: int = Field(..., description="Cart item unique identifier")
    product: ProductSummaryResponse = Field(..., description="Product information")
    size: SizeEnum = Field(..., description="Selected size")
    quantity: int = Field(..., gt=0, description="Item quantity")
    subtotal: Decimal = Field(..., ge=0, description="Subtotal for this item (price × quantity)")
    added_date: datetime = Field(..., description="Date when item was added to cart")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "product": {
                    "id": 1,
                    "name": "Premium Running T-Shirt",
                    "color": "Navy Blue",
                    "gender": "male",
                    "brand": "spoXpro",
                    "price": "29.99",
                    "article_number": "SPX-RUN-001",
                    "images": ["image1.jpg"],
                    "product_views": 127,
                    "available_sizes": ["M", "L", "XL"]
                },
                "size": "M",
                "quantity": 2,
                "subtotal": "59.98",
                "added_date": "2024-01-15T10:30:00Z"
            }
        }


class CartResponse(BaseModel):
    """Response model for cart information."""
    
    items: List[CartItemResponse] = Field(..., description="List of cart items")
    total: Decimal = Field(..., ge=0, description="Total cart value")
    item_count: int = Field(..., ge=0, description="Total number of items in cart")
    
    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "product": {
                            "id": 1,
                            "name": "Premium Running T-Shirt",
                            "color": "Navy Blue",
                            "gender": "male",
                            "brand": "spoXpro",
                            "price": "29.99",
                            "article_number": "SPX-RUN-001",
                            "images": ["image1.jpg"],
                            "product_views": 127,
                            "available_sizes": ["M", "L", "XL"]
                        },
                        "size": "M",
                        "quantity": 2,
                        "subtotal": "59.98",
                        "added_date": "2024-01-15T10:30:00Z"
                    }
                ],
                "total": "59.98",
                "item_count": 2
            }
        }


class CartValidationResponse(BaseModel):
    """Response model for cart validation."""
    
    valid: bool = Field(..., description="Whether the cart is valid for checkout")
    issues: List[Dict[str, Any]] = Field(default=[], description="List of validation issues")
    
    class Config:
        schema_extra = {
            "example": {
                "valid": False,
                "issues": [
                    {
                        "item_id": 1,
                        "issue": "insufficient_inventory",
                        "message": "Only 1 available, but 2 requested",
                        "available_quantity": 1,
                        "requested_quantity": 2
                    }
                ]
            }
        }


class CreateOrderRequest(BaseModel):
    """Request model for creating an order."""
    
    shipping_address: str = Field(..., min_length=10, max_length=500, description="Shipping address")
    payment_method: str = Field(..., description="Payment method")
    notes: Optional[str] = Field(None, max_length=500, description="Order notes")
    
    @validator('payment_method')
    def validate_payment_method(cls, v):
        """Validate payment method."""
        valid_methods = ["credit_card", "debit_card", "paypal", "bank_transfer", "cash_on_delivery"]
        if v not in valid_methods:
            raise ValueError(f'Payment method must be one of: {", ".join(valid_methods)}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "shipping_address": "123 Main St, Apt 4B, New York, NY 10001",
                "payment_method": "credit_card",
                "notes": "Please deliver after 6 PM"
            }
        }


class OrderItemResponse(BaseModel):
    """Response model for order item information."""
    
    id: int = Field(..., description="Order item unique identifier")
    product_name: str = Field(..., description="Product name at time of order")
    product_id: int = Field(..., description="Product ID")
    size: SizeEnum = Field(..., description="Ordered size")
    quantity: int = Field(..., gt=0, description="Ordered quantity")
    price_at_time: Decimal = Field(..., ge=0, description="Product price when order was placed")
    subtotal: Decimal = Field(..., ge=0, description="Subtotal for this item")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "product_name": "Premium Running T-Shirt",
                "product_id": 1,
                "size": "M",
                "quantity": 2,
                "price_at_time": "29.99",
                "subtotal": "59.98"
            }
        }


class OrderResponse(BaseModel):
    """Response model for order information."""
    
    id: int = Field(..., description="Order unique identifier")
    items: List[OrderItemResponse] = Field(..., description="List of order items")
    total_amount: Decimal = Field(..., ge=0, description="Total order amount")
    status: str = Field(..., description="Order status")
    created_date: datetime = Field(..., description="Order creation timestamp")
    shipping_address: Optional[str] = Field(None, description="Shipping address")
    payment_method: Optional[str] = Field(None, description="Payment method")
    notes: Optional[str] = Field(None, description="Order notes")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "items": [
                    {
                        "id": 1,
                        "product_name": "Premium Running T-Shirt",
                        "product_id": 1,
                        "size": "M",
                        "quantity": 2,
                        "price_at_time": "29.99",
                        "subtotal": "59.98"
                    }
                ],
                "total_amount": "59.98",
                "status": "pending",
                "created_date": "2024-01-15T10:30:00Z",
                "shipping_address": "123 Main St, Apt 4B, New York, NY 10001",
                "payment_method": "credit_card",
                "notes": "Please deliver after 6 PM"
            }
        }


class OrderListResponse(BaseModel):
    """Response model for paginated order list."""
    
    orders: List[OrderResponse] = Field(..., description="List of orders")
    total_count: int = Field(..., ge=0, description="Total number of orders")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")
    
    class Config:
        schema_extra = {
            "example": {
                "orders": [
                    {
                        "id": 1,
                        "items": [],
                        "total_amount": "59.98",
                        "status": "pending",
                        "created_date": "2024-01-15T10:30:00Z"
                    }
                ],
                "total_count": 5,
                "page": 1,
                "page_size": 10,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False
            }
        }


class UpdateOrderStatusRequest(BaseModel):
    """Request model for updating order status."""
    
    status: str = Field(..., description="New order status")
    
    @validator('status')
    def validate_status(cls, v):
        """Validate order status."""
        valid_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "status": "confirmed"
            }
        }


class UserStatisticsResponse(BaseModel):
    """Response model for user statistics."""
    
    total_orders: int = Field(..., ge=0, description="Total number of orders")
    total_spent: Decimal = Field(..., ge=0, description="Total amount spent")
    average_order_value: Decimal = Field(..., ge=0, description="Average order value")
    favorite_categories: List[str] = Field(..., description="Most purchased categories")
    recent_orders: List[OrderResponse] = Field(..., description="Recent orders")
    
    class Config:
        schema_extra = {
            "example": {
                "total_orders": 12,
                "total_spent": "459.88",
                "average_order_value": "38.32",
                "favorite_categories": ["Men's Clothing", "Running Gear"],
                "recent_orders": []
            }
        }


class WishlistItemResponse(BaseModel):
    """Response model for wishlist item."""
    
    id: int = Field(..., description="Wishlist item unique identifier")
    product: ProductSummaryResponse = Field(..., description="Product information")
    added_date: datetime = Field(..., description="Date when item was added to wishlist")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "product": {
                    "id": 1,
                    "name": "Premium Running T-Shirt",
                    "color": "Navy Blue",
                    "gender": "male",
                    "brand": "spoXpro",
                    "price": "29.99",
                    "article_number": "SPX-RUN-001",
                    "images": ["image1.jpg"],
                    "product_views": 127,
                    "available_sizes": ["M", "L", "XL"]
                },
                "added_date": "2024-01-15T10:30:00Z"
            }
        }


class WishlistResponse(BaseModel):
    """Response model for wishlist."""
    
    items: List[WishlistItemResponse] = Field(..., description="List of wishlist items")
    total_count: int = Field(..., ge=0, description="Total number of items in wishlist")
    
    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "product": {
                            "id": 1,
                            "name": "Premium Running T-Shirt",
                            "color": "Navy Blue",
                            "gender": "male",
                            "brand": "spoXpro",
                            "price": "29.99",
                            "article_number": "SPX-RUN-001",
                            "images": ["image1.jpg"],
                            "product_views": 127,
                            "available_sizes": ["M", "L", "XL"]
                        },
                        "added_date": "2024-01-15T10:30:00Z"
                    }
                ],
                "total_count": 1
            }
        }


class AddToWishlistRequest(BaseModel):
    """Request model for adding items to wishlist."""
    
    product_id: int = Field(..., gt=0, description="Product ID to add to wishlist")
    
    class Config:
        schema_extra = {
            "example": {
                "product_id": 1
            }
        }


class CartMigrationRequest(BaseModel):
    """Request model for migrating guest cart to user account."""
    
    guest_cookie: str = Field(..., description="Guest cookie to migrate from")
    
    class Config:
        schema_extra = {
            "example": {
                "guest_cookie": "guest_abc123def456ghi789"
            }
        }


class CartMigrationResponse(BaseModel):
    """Response model for cart migration."""
    
    success: bool = Field(..., description="Whether migration was successful")
    migrated_items: int = Field(..., ge=0, description="Number of items migrated")
    message: str = Field(..., description="Migration result message")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "migrated_items": 3,
                "message": "Successfully migrated 3 items from guest cart"
            }
        }