"""
API Documentation for spoXpro E-commerce Backend

This module contains comprehensive API documentation, examples,
and usage guidelines for the spoXpro backend API.
"""

from typing import Dict, Any

# API Documentation Content
API_DESCRIPTION = """
# spoXpro E-commerce Backend API

A comprehensive sports clothing e-commerce platform backend built with FastAPI.

## Features

- **Product Management**: Browse and search sports clothing products
- **User Authentication**: JWT-based authentication with guest support
- **Shopping Cart**: Add, update, and manage cart items
- **Order Processing**: Complete checkout and order history
- **Admin Panel**: Administrative functionality for managing the platform

## Authentication

The API supports two types of authentication:

### JWT Authentication (Registered Users)
- Register or login to receive a JWT token
- Include token in Authorization header: `Bearer <token>`
- Required for user profile, order history, and admin operations

### Cookie Authentication (Guest Users)
- Automatic cookie generation for first-time visitors
- Supports cart operations without registration
- Limited to cart functionality only

## API Endpoints

### Authentication (`/auth`)
- User registration and login
- Email verification
- Guest cookie management
- Token validation

### Store (`/store`)
- Product catalog with filtering and search
- Product details with view tracking
- Helper data (categories, types, materials)

### User (`/user`)
- User profile management
- Shopping cart operations
- Order history and creation

## Error Handling

All API errors follow a consistent JSON structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": {},
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## Rate Limiting

API endpoints are rate-limited to ensure fair usage and system stability.

## Data Formats

- All timestamps are in ISO 8601 format (UTC)
- Prices are in decimal format with 2 decimal places
- Product sizes: XXS, XS, S, M, L, XL, XXL, XXXL, XXXXL
"""

# API Examples
API_EXAMPLES = {
    "user_registration": {
        "description": "Register a new user account",
        "request": {
            "method": "POST",
            "url": "/auth/register",
            "body": {
                "email": "user@example.com",
                "password": "securepassword123",
                "phone": "+1234567890"
            }
        },
        "response": {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "token_type": "bearer",
            "user_id": 1
        }
    },
    "product_search": {
        "description": "Search products with filters",
        "request": {
            "method": "GET",
            "url": "/store/products?category=shirts&gender=male&min_price=20&max_price=100"
        },
        "response": {
            "products": [
                {
                    "id": 1,
                    "name": "Athletic Performance Shirt",
                    "description": "High-performance athletic shirt",
                    "price": 49.99,
                    "category": "shirts",
                    "gender": "male",
                    "sizes": [
                        {"size": "M", "quantity": 10},
                        {"size": "L", "quantity": 5}
                    ]
                }
            ],
            "total": 1,
            "page": 1,
            "per_page": 20
        }
    },
    "add_to_cart": {
        "description": "Add item to shopping cart",
        "request": {
            "method": "POST",
            "url": "/user/cart/add",
            "headers": {
                "Authorization": "Bearer <token>"
            },
            "body": {
                "product_id": 1,
                "size": "M",
                "quantity": 2
            }
        },
        "response": {
            "message": "Item added to cart successfully",
            "cart_item_id": 123
        }
    },
    "create_order": {
        "description": "Create a new order from cart",
        "request": {
            "method": "POST",
            "url": "/user/orders/create",
            "headers": {
                "Authorization": "Bearer <token>"
            },
            "body": {
                "shipping_address": "123 Main St, City, State 12345",
                "payment_method": "credit_card"
            }
        },
        "response": {
            "order_id": 456,
            "total_amount": 99.98,
            "status": "pending",
            "created_date": "2024-01-01T12:00:00Z"
        }
    }
}

# Error Examples
ERROR_EXAMPLES = {
    "validation_error": {
        "status_code": 400,
        "response": {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": {
                    "email": ["Invalid email format"],
                    "password": ["Password must be at least 8 characters"]
                },
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
    },
    "authentication_error": {
        "status_code": 401,
        "response": {
            "error": {
                "code": "AUTHENTICATION_ERROR",
                "message": "Invalid or expired token",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
    },
    "not_found_error": {
        "status_code": 404,
        "response": {
            "error": {
                "code": "NOT_FOUND",
                "message": "Product not found",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
    },
    "inventory_error": {
        "status_code": 409,
        "response": {
            "error": {
                "code": "INSUFFICIENT_INVENTORY",
                "message": "Not enough inventory available",
                "details": {
                    "requested": 5,
                    "available": 2
                },
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
    }
}


def get_api_documentation() -> Dict[str, Any]:
    """Get complete API documentation."""
    return {
        "description": API_DESCRIPTION,
        "examples": API_EXAMPLES,
        "error_examples": ERROR_EXAMPLES,
        "version": "1.0.0"
    }


def get_openapi_tags() -> list:
    """Get OpenAPI tags for endpoint organization."""
    return [
        {
            "name": "root",
            "description": "Root endpoints and application information"
        },
        {
            "name": "health",
            "description": "Health check and system status endpoints"
        },
        {
            "name": "authentication",
            "description": "User authentication, registration, and session management"
        },
        {
            "name": "store",
            "description": "Product catalog, search, and store information"
        },
        {
            "name": "user",
            "description": "User profile, cart operations, and order management"
        },
        {
            "name": "admin",
            "description": "Administrative endpoints for platform management"
        }
    ]