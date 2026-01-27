#!/usr/bin/env python3
"""
Simple test to verify product view count increment functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.services.product_service import ProductService
from db.models.product import Product, ProductSize, ProductType, Category, SportType, Material
from tests.conftest import create_test_db_session, create_sample_helper_data
from decimal import Decimal


def test_product_view_count_increment():
    """Test that product view count increments correctly."""
    print("Testing product view count increment...")
    
    with create_test_db_session() as session:
        # Create helper data
        helper_data = create_sample_helper_data(session)
        
        # Create product service
        product_service = ProductService(session)
        
        # Create a test product
        product = Product(
            name="Test Product",
            description="Test Description",
            product_type_id=helper_data["product_type"].id,
            category_id=helper_data["category"].id,
            sport_type_id=helper_data["sport_type"].id,
            color="Blue",
            gender="unisex",
            brand="spoXpro",
            price=Decimal("29.99"),
            reviews=[{"rating": 5, "comment": "Great!"}],
            article_number="TEST123",
            images=["test.jpg"],
            material_id=helper_data["material"].id,
            product_views=0
        )
        
        session.add(product)
        session.flush()
        
        # Add a size
        size = ProductSize(
            product_id=product.id,
            size="M",
            quantity=10
        )
        session.add(size)
        session.commit()
        
        # Test 1: Initial view count should be 0
        assert product.product_views == 0, f"Initial view count should be 0, got {product.product_views}"
        print("✓ Initial view count is 0")
        
        # Test 2: Increment view count
        success = product_service.increment_product_views(product.id)
        assert success, "View count increment should succeed"
        
        session.refresh(product)
        assert product.product_views == 1, f"View count should be 1 after increment, got {product.product_views}"
        print("✓ View count incremented to 1")
        
        # Test 3: Multiple increments
        for i in range(2, 6):
            success = product_service.increment_product_views(product.id)
            assert success, f"View count increment {i} should succeed"
            session.refresh(product)
            assert product.product_views == i, f"View count should be {i}, got {product.product_views}"
        
        print("✓ Multiple increments work correctly")
        
        # Test 4: Non-existent product
        success = product_service.increment_product_views(999999)
        assert not success, "Incrementing non-existent product should return False"
        print("✓ Non-existent product handling works")
        
        print("All tests passed! ✓")


if __name__ == "__main__":
    test_product_view_count_increment()