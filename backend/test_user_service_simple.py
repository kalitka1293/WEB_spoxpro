#!/usr/bin/env python3
"""
Simple test to verify user service functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.services.user_service import UserService
from tests.conftest import create_test_db_session


def test_user_service_basic():
    """Test basic user service functionality."""
    print("Testing user service...")
    
    with create_test_db_session() as session:
        # Create user service
        user_service = UserService(session)
        
        # Test 1: Create a user
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "phone": "+1234567890"
        }
        
        user = user_service.create_user(user_data)
        assert user is not None, "User creation should succeed"
        assert user.email == "test@example.com", "Email should match"
        assert user.phone == "+1234567890", "Phone should match"
        assert user.password_hash != "testpassword123", "Password should be hashed"
        print("✓ User creation works")
        
        # Test 2: Get user by ID
        retrieved_user = user_service.get_user_by_id(user.id)
        assert retrieved_user is not None, "User should be found by ID"
        assert retrieved_user.email == user.email, "Retrieved user should match"
        print("✓ Get user by ID works")
        
        # Test 3: Get user by email
        retrieved_user = user_service.get_user_by_email("test@example.com")
        assert retrieved_user is not None, "User should be found by email"
        assert retrieved_user.id == user.id, "Retrieved user should match"
        print("✓ Get user by email works")
        
        # Test 4: Authenticate user
        authenticated_user = user_service.authenticate_user("test@example.com", "testpassword123")
        assert authenticated_user is not None, "Authentication should succeed"
        assert authenticated_user.id == user.id, "Authenticated user should match"
        print("✓ User authentication works")
        
        # Test 5: Authentication with wrong password
        authenticated_user = user_service.authenticate_user("test@example.com", "wrongpassword")
        assert authenticated_user is None, "Authentication should fail with wrong password"
        print("✓ Authentication rejection works")
        
        # Test 6: Verification code
        success = user_service.create_verification_code("test@example.com", "123456")
        assert success, "Verification code creation should succeed"
        print("✓ Verification code creation works")
        
        # Test 7: Verify code
        verified = user_service.verify_code("test@example.com", "123456")
        assert verified, "Code verification should succeed"
        print("✓ Code verification works")
        
        # Test 8: Verify code again (should fail - one-time use)
        verified = user_service.verify_code("test@example.com", "123456")
        assert not verified, "Code verification should fail on second use"
        print("✓ One-time code usage works")
        
        print("All tests passed! ✓")


if __name__ == "__main__":
    test_user_service_basic()