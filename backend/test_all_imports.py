#!/usr/bin/env python3
"""
Comprehensive import test for spoXpro backend.
Tests all critical imports to ensure no import errors exist.
"""

import sys
import os
sys.path.append('.')

def test_imports():
    """Test all critical imports."""
    print("🔍 Testing all critical imports...")
    
    # Test database models
    try:
        from db.models.user import User, VerificationCode
        from db.models.order import CartItem, Order, OrderItem
        from db.models.product import Product, ProductSize, ProductType, Category, SportType, Material
        print("✓ Database models import OK")
    except Exception as e:
        print(f"✗ Database models import ERROR: {e}")
        return False
    
    # Test database services
    try:
        from db.services.user_service import UserService
        from db.services.cart_service import CartService as DBCartService
        from db.services.order_service import OrderService as DBOrderService
        from db.services.product_service import ProductService
        print("✓ Database services import OK")
    except Exception as e:
        print(f"✗ Database services import ERROR: {e}")
        return False
    
    # Test business services
    try:
        from service.auth_service import AuthService
        from service.cart_service import CartService as BusinessCartService
        from service.order_service import OrderProcessingService
        print("✓ Business services import OK")
    except Exception as e:
        print(f"✗ Business services import ERROR: {e}")
        return False
    
    # Test DTOs
    try:
        from DTO.auth import UserRegistrationRequest, AuthResponse
        from DTO.user import AddToCartRequest, CartResponse
        from DTO.store import ProductResponse, ProductListResponse
        print("✓ DTO models import OK")
    except Exception as e:
        print(f"✗ DTO models import ERROR: {e}")
        return False
    
    # Test routes
    try:
        from routes.auth import router as auth_router
        from routes.user import router as user_router
        from routes.store import router as store_router
        print("✓ Route modules import OK")
    except Exception as e:
        print(f"✗ Route modules import ERROR: {e}")
        return False
    
    # Test main application
    try:
        from main import app
        print("✓ Main application import OK")
    except Exception as e:
        print(f"✗ Main application import ERROR: {e}")
        return False
    
    # Test middleware
    try:
        from middleware.exception_handlers import (
            BusinessLogicError, AuthenticationError, ResourceNotFoundError
        )
        print("✓ Middleware import OK")
    except Exception as e:
        print(f"✗ Middleware import ERROR: {e}")
        return False
    
    print("\n🎉 ALL IMPORTS SUCCESSFUL!")
    print("✅ No import errors found in the project")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)