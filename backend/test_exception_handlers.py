"""
Simple test for exception handlers functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from middleware.exception_handlers import (
    register_exception_handlers, AuthenticationError, 
    ResourceNotFoundError, InsufficientInventoryError
)

# Create test app
app = FastAPI()
register_exception_handlers(app)

@app.get("/test-http-error")
async def test_http_error():
    raise HTTPException(status_code=404, detail="Test resource not found")

@app.get("/test-auth-error")
async def test_auth_error():
    raise AuthenticationError("Invalid credentials")

@app.get("/test-resource-error")
async def test_resource_error():
    raise ResourceNotFoundError("Product", "123")

@app.get("/test-inventory-error")
async def test_inventory_error():
    raise InsufficientInventoryError(product_id=456, requested_quantity=10, available_quantity=3)

@app.get("/test-generic-error")
async def test_generic_error():
    raise ValueError("This is a test generic error")

# Test client
with TestClient(app) as client:
    
    def test_exception_handlers():
        """Test all exception handlers."""
        print("Testing exception handlers...")
        
        # Test HTTP exception
        response = client.get("/test-http-error")
        print(f"HTTP Error Response: {response.status_code} - {response.json()}")
        assert response.status_code == 404
        assert "error" in response.json()
        
        # Test authentication error
        response = client.get("/test-auth-error")
        print(f"Auth Error Response: {response.status_code} - {response.json()}")
        assert response.status_code == 401
        assert response.json()["error"]["type"] == "authentication_error"
        
        # Test resource not found error
        response = client.get("/test-resource-error")
        print(f"Resource Error Response: {response.status_code} - {response.json()}")
        assert response.status_code == 404
        assert response.json()["error"]["type"] == "resource_not_found"
        
        # Test inventory error
        response = client.get("/test-inventory-error")
        print(f"Inventory Error Response: {response.status_code} - {response.json()}")
        assert response.status_code == 409
        assert response.json()["error"]["type"] == "insufficient_inventory"
        
        # Test generic error
        response = client.get("/test-generic-error")
        print(f"Generic Error Response: {response.status_code} - {response.json()}")
        assert response.status_code == 500
        assert response.json()["error"]["type"] == "internal_server_error"
        
        print("All exception handler tests passed!")
    
    if __name__ == "__main__":
        test_exception_handlers()