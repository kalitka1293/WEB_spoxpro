"""
Simple test for exception handlers functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from middleware.exception_handlers import (
    ErrorResponse, AuthenticationError, ResourceNotFoundError, 
    InsufficientInventoryError, BusinessLogicError
)

def test_error_response():
    """Test ErrorResponse class."""
    print("Testing ErrorResponse class...")
    
    error = ErrorResponse("test_error", "Test message", {"detail": "test"}, 400)
    response_dict = error.to_dict()
    
    assert response_dict["error"]["type"] == "test_error"
    assert response_dict["error"]["message"] == "Test message"
    assert response_dict["error"]["status_code"] == 400
    assert response_dict["error"]["details"]["detail"] == "test"
    
    print("ErrorResponse test passed!")

def test_custom_exceptions():
    """Test custom business logic exceptions."""
    print("Testing custom exceptions...")
    
    # Test AuthenticationError
    auth_error = AuthenticationError("Invalid token")
    assert auth_error.message == "Invalid token"
    assert auth_error.error_code == "authentication_error"
    assert auth_error.status_code == 401
    
    # Test ResourceNotFoundError
    resource_error = ResourceNotFoundError("Product", "123")
    assert "Product not found (ID: 123)" in resource_error.message
    assert resource_error.error_code == "resource_not_found"
    assert resource_error.status_code == 404
    
    # Test InsufficientInventoryError
    inventory_error = InsufficientInventoryError(456, 10, 3)
    assert "product 456" in inventory_error.message
    assert "requested 10" in inventory_error.message
    assert "available 3" in inventory_error.message
    assert inventory_error.error_code == "insufficient_inventory"
    assert inventory_error.status_code == 409
    
    print("Custom exceptions test passed!")

def test_exception_handlers():
    """Test exception handler functionality."""
    print("Testing exception handlers...")
    
    # Test error response creation
    test_error_response()
    
    # Test custom exceptions
    test_custom_exceptions()
    
    print("All exception handler tests passed!")

if __name__ == "__main__":
    test_exception_handlers()