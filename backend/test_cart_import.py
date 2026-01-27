#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

print("Testing cart service import step by step...")

print("1. Testing basic imports...")
try:
    from typing import Optional, List, Dict, Any
    from decimal import Decimal
    print("✓ Basic imports OK")
except Exception as e:
    print(f"✗ Basic imports ERROR: {e}")
    exit(1)

print("2. Testing database imports...")
try:
    from db.services.cart_service import CartService as DBCartService
    print("✓ DBCartService import OK")
except Exception as e:
    print(f"✗ DBCartService import ERROR: {e}")
    exit(1)

print("3. Testing auth service import...")
try:
    from service.auth_service import AuthService
    print("✓ AuthService import OK")
except Exception as e:
    print(f"✗ AuthService import ERROR: {e}")
    exit(1)

print("4. Testing logger import...")
try:
    from logs.log_store import get_logger
    print("✓ Logger import OK")
except Exception as e:
    print(f"✗ Logger import ERROR: {e}")
    exit(1)

print("5. Testing exception handlers import...")
try:
    from middleware.exception_handlers import (
        ResourceNotFoundError, InvalidOperationError, InsufficientInventoryError
    )
    print("✓ Exception handlers import OK")
except Exception as e:
    print(f"✗ Exception handlers import ERROR: {e}")
    exit(1)

print("6. Testing cart service class definition...")
try:
    logger = get_logger(__name__)
    
    class CartService:
        """Business logic service for cart operations."""
        
        def __init__(self, db_cart_service: DBCartService, auth_service: AuthService):
            self.db_cart_service = db_cart_service
            self.auth_service = auth_service
        
        def test_method(self):
            return "test"
    
    print("✓ CartService class definition OK")
    
    # Test instantiation
    print("7. Testing service instantiation...")
    # We can't actually instantiate without proper dependencies, but we can check the class
    print(f"CartService class: {CartService}")
    print("✓ All tests passed!")
    
except Exception as e:
    print(f"✗ CartService class definition ERROR: {e}")
    import traceback
    traceback.print_exc()