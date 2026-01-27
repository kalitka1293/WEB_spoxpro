#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

print("Debug: Testing cart service import with detailed error handling...")

try:
    print("1. Importing typing...")
    from typing import Optional, List, Dict, Any
    from decimal import Decimal
    print("✓ Basic imports OK")
    
    print("2. Importing database services...")
    from db.services.cart_service import CartService as DBCartService
    print("✓ DBCartService import OK")
    
    print("3. Importing auth service...")
    from service.auth_service import AuthService
    print("✓ AuthService import OK")
    
    print("4. Importing logger...")
    from logs.log_store import get_logger
    print("✓ Logger import OK")
    
    print("5. Importing exception handlers...")
    from middleware.exception_handlers import (
        ResourceNotFoundError, InvalidOperationError, InsufficientInventoryError
    )
    print("✓ Exception handlers import OK")
    
    print("6. Creating logger...")
    logger = get_logger(__name__)
    print("✓ Logger created OK")
    
    print("7. Defining CartService class...")
    
    class CartService:
        """Business logic service for cart operations."""
        
        def __init__(self, db_cart_service: DBCartService, auth_service: AuthService):
            self.db_cart_service = db_cart_service
            self.auth_service = auth_service
    
    print("✓ CartService class defined OK")
    print(f"CartService: {CartService}")
    
    print("8. Testing module import...")
    import importlib
    import service.cart_service
    importlib.reload(service.cart_service)
    print("✓ Module import OK")
    
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()