"""
Property-based tests for product view count increment functionality.

**Feature: spoxpro-backend, Property 3: Product View Count Increment**
**Validates: Requirements 1.3**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from decimal import Decimal
from typing import List, Dict, Any
import uuid

from db.services.product_service import ProductService
from db.models.product import Product, ProductSize, ProductType, Category, SportType, Material
from tests.conftest import create_test_db_session, create_sample_helper_data


# Valid clothing sizes as per requirements
VALID_SIZES = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "XXXXL"]


@st.composite
def product_data_strategy(draw):
    """Generate valid product data for testing."""
    return {
        "name": draw(st.text(min_size=1, max_size=100)),
        "description": draw(st.text(min_size=1, max_size=500)),
        "color": draw(st.text(min_size=1, max_size=50)),
        "gender": draw(st.sampled_from(["male", "female", "unisex"])),
        "brand": draw(st.text(min_size=1, max_size=50)),
        "price": draw(st.decimals(min_value=Decimal("0.01"), max_value=Decimal("9999.99"), places=2)),
        "reviews": draw(st.lists(st.dictionaries(
            st.text(min_size=1, max_size=20), 
            st.one_of(st.text(max_size=100), st.integers(min_value=1, max_value=5)),
            min_size=1, max_size=3
        ), max_size=5)),
        "article_number": draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")))),
        "images": draw(st.lists(st.text(min_size=1, max_size=200), min_size=1, max_size=5)),
        "sizes": draw(st.lists(
            st.tuples(
                st.sampled_from(VALID_SIZES),
                st.integers(min_value=0, max_value=1000)
            ),
            min_size=1, max_size=len(VALID_SIZES), unique_by=lambda x: x[0]
        ))
    }


class TestProductViewCountProperties:
    """Property-based tests for product view count increment functionality."""

    @given(product_data=product_data_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_product_view_count_increment_property(self, product_data):
        """
        Property 3: Product View Count Increment
        For any product, viewing the product should increase its view count by exactly one from the previous count.
        
        **Validates: Requirements 1.3**
        """
        with create_test_db_session() as session:
            # Create helper data
            helper_data = create_sample_helper_data(session)
            
            # Create product service
            product_service = ProductService(session)
            
            # Create a product with the generated data
            product = Product(
                name=product_data["name"],
                description=product_data["description"],
                product_type_id=helper_data["product_type"].id,
                category_id=helper_data["category"].id,
                sport_type_id=helper_data["sport_type"].id,
                color=product_data["color"],
                gender=product_data["gender"],
                brand=product_data["brand"],
                price=product_data["price"],
                reviews=product_data["reviews"],
                article_number=product_data["article_number"],
                images=product_data["images"],
                material_id=helper_data["material"].id,
                product_views=0  # Start with 0 views
            )
            
            session.add(product)
            session.flush()  # Get the ID
            
            # Add sizes
            for size_name, quantity in product_data["sizes"]:
                size = ProductSize(
                    product_id=product.id,
                    size=size_name,
                    quantity=quantity
                )
                session.add(size)
            
            session.commit()
            
            # Get initial view count
            initial_count = product.product_views
            
            # Increment view count
            success = product_service.increment_product_views(product.id)
            
            # Verify the increment was successful
            assert success, "View count increment should succeed"
            
            # Refresh the product to get updated data
            session.refresh(product)
            
            # Property: View count should be exactly one more than before
            assert product.product_views == initial_count + 1, \
                f"View count should be {initial_count + 1}, but got {product.product_views}"

    @given(
        product_data=product_data_strategy(),
        increment_count=st.integers(min_value=1, max_value=50)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_multiple_view_increments_property(self, product_data, increment_count):
        """
        Property: Multiple view increments should accumulate correctly.
        For any product and any number of view operations, the final count should equal 
        the initial count plus the number of view operations.
        
        **Validates: Requirements 1.3**
        """
        with create_test_db_session() as session:
            # Create helper data
            helper_data = create_sample_helper_data(session)
            
            # Create product service
            product_service = ProductService(session)
            
            # Create a product with the generated data
            product = Product(
                name=product_data["name"],
                description=product_data["description"],
                product_type_id=helper_data["product_type"].id,
                category_id=helper_data["category"].id,
                sport_type_id=helper_data["sport_type"].id,
                color=product_data["color"],
                gender=product_data["gender"],
                brand=product_data["brand"],
                price=product_data["price"],
                reviews=product_data["reviews"],
                article_number=product_data["article_number"],
                images=product_data["images"],
                material_id=helper_data["material"].id,
                product_views=0  # Start with 0 views
            )
            
            session.add(product)
            session.flush()  # Get the ID
            
            # Add sizes
            for size_name, quantity in product_data["sizes"]:
                size = ProductSize(
                    product_id=product.id,
                    size=size_name,
                    quantity=quantity
                )
                session.add(size)
            
            session.commit()
            
            # Get initial view count
            initial_count = product.product_views
            
            # Perform multiple increments
            for _ in range(increment_count):
                success = product_service.increment_product_views(product.id)
                assert success, "Each view count increment should succeed"
            
            # Refresh the product to get updated data
            session.refresh(product)
            
            # Property: Final count should equal initial count plus number of increments
            expected_count = initial_count + increment_count
            assert product.product_views == expected_count, \
                f"View count should be {expected_count}, but got {product.product_views}"

    @given(product_data=product_data_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_view_count_nonexistent_product_property(self, product_data):
        """
        Property: Attempting to increment view count for non-existent product should fail gracefully.
        For any non-existent product ID, the increment operation should return False.
        
        **Validates: Requirements 1.3**
        """
        with create_test_db_session() as session:
            # Create product service
            product_service = ProductService(session)
            
            # Use a non-existent product ID (very high number)
            nonexistent_id = 999999
            
            # Attempt to increment view count for non-existent product
            success = product_service.increment_product_views(nonexistent_id)
            
            # Property: Operation should fail gracefully
            assert not success, "Incrementing view count for non-existent product should return False"