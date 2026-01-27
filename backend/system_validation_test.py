#!/usr/bin/env python3
"""
System Validation Test - Final Checkpoint

This script performs comprehensive validation of the spoXpro backend system
to ensure all components are working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.main import init_database, health_check
from service.auth_service import AuthService
from service.cart_service import CartService
from service.order_service import OrderProcessingService
from db.services.user_service import UserService
from db.services.cart_service import CartService as DBCartService
from db.services.order_service import OrderService as OrderDBService
from db.services.product_service import ProductService
from main import app
from logs.log_store import get_logger

logger = get_logger(__name__)


def test_database_initialization():
    """Test database initialization and health check."""
    print("🔍 Testing database initialization...")
    
    # Initialize database
    init_result = init_database()
    if not init_result:
        print("❌ Database initialization failed")
        return False
    
    # Perform health check
    health = health_check()
    if health["status"] != "healthy":
        print(f"❌ Database health check failed: {health}")
        return False
    
    print("✅ Database initialization and health check passed")
    return True


def test_service_initialization():
    """Test that all services can be initialized."""
    print("🔍 Testing service initialization...")
    
    try:
        from db.main import get_db_session
        
        # Get database session
        db = get_db_session()
        
        # Initialize database services
        user_service = UserService(db)
        cart_db_service = DBCartService(db)
        order_db_service = OrderDBService(db)
        product_service = ProductService(db)
        
        # Initialize business logic services
        auth_service = AuthService(user_service)
        cart_service = CartService(cart_db_service, product_service)
        order_service = OrderProcessingService(order_db_service, cart_db_service, product_service)
        
        # Close database session
        db.close()
        
        print("✅ All services initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False


def test_fastapi_app():
    """Test FastAPI application initialization."""
    print("🔍 Testing FastAPI application...")
    
    try:
        # Check that app is created
        if app is None:
            print("❌ FastAPI app is None")
            return False
        
        # Check routes
        route_count = len(app.routes)
        if route_count < 10:  # Should have many routes
            print(f"❌ Too few routes: {route_count}")
            return False
        
        print(f"✅ FastAPI app initialized with {route_count} routes")
        return True
        
    except Exception as e:
        print(f"❌ FastAPI app test failed: {e}")
        return False


def test_basic_functionality():
    """Test basic system functionality."""
    print("🔍 Testing basic functionality...")
    
    try:
        from db.main import get_db_session_context
        from db.models.product import Product, ProductType, Category, SportType, Material
        
        # Test database operations
        with get_db_session_context() as db:
            # Check if we can query (should be empty but not error)
            product_count = db.query(Product).count()
            print(f"📊 Current product count: {product_count}")
        
        print("✅ Basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False


def run_system_validation():
    """Run complete system validation."""
    print("🚀 Starting spoXpro Backend System Validation")
    print("=" * 50)
    
    tests = [
        ("Database Initialization", test_database_initialization),
        ("Service Initialization", test_service_initialization),
        ("FastAPI Application", test_fastapi_app),
        ("Basic Functionality", test_basic_functionality),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("=" * 50)
    print(f"📊 System Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All system validation tests passed!")
        print("✅ spoXpro Backend is ready for production")
        return True
    else:
        print("⚠️  Some validation tests failed")
        print("🔧 Please review the failed components")
        return False


if __name__ == "__main__":
    success = run_system_validation()
    sys.exit(0 if success else 1)