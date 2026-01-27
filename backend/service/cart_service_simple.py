"""
Simple cart service for testing imports.
"""

class CartService:
    """Simple cart service."""
    
    def __init__(self, db_cart_service, auth_service):
        self.db_cart_service = db_cart_service
        self.auth_service = auth_service
    
    def test_method(self):
        return "test"