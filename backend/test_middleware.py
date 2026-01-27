#!/usr/bin/env python3
"""
Simple test for authentication middleware.
"""

import sys
import os
sys.path.append('.')

def test_middleware():
    """Test middleware imports and basic functionality."""
    print("🔍 Testing middleware...")
    
    try:
        from middleware.auth_middleware import validate_jwt_token, validate_guest_cookie
        from middleware.dependencies import get_auth_service
        print("✓ Middleware imports OK")
    except Exception as e:
        print(f"✗ Middleware import ERROR: {e}")
        return False
    
    try:
        # Test auth service creation
        auth_service = get_auth_service()
        print("✓ Auth service creation OK")
    except Exception as e:
        print(f"✗ Auth service ERROR: {e}")
        return False
    
    try:
        # Test guest cookie validation with invalid cookie
        result = validate_guest_cookie("invalid_cookie")
        print(f"✓ Guest cookie validation OK (result: {result})")
    except Exception as e:
        print(f"✗ Guest cookie validation ERROR: {e}")
        return False
    
    print("✅ Middleware tests passed!")
    return True

if __name__ == "__main__":
    success = test_middleware()
    sys.exit(0 if success else 1)