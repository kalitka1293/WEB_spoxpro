"""
Property-based tests for product database models.

**Feature: spoxpro-backend, Property 1: Product Data Integrity**
**Validates: Requirements 1.1, 1.4**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any
import json

from backend.db.models.product import Product, ProductSize, ProductType, Category, SportType, Material
from .conftest import create_test_db_session, create_sample_helper_data


# Valid clothing sizes as per requirements
VALID_SIZES = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "XXXXL"]
VALID_GENDERS = ["male", "female", "unisex"]


# Hypothesis strategies for generating test data
@st.composite
def product_data_strategy(draw):
    """Generate valid product data for testing."""
    return {
        "name": draw(st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")))),
        "description": draw(st.text(min_size=1, max_size=1000, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po")))),
        "color": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll")))),
        "gender": draw(st.sampled_from(VALID_GENDERS)),
        "brand": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")))),
        "price": draw(st.decimals(min_value=Decimal("0.01"), max_value=Decimal("9999.99"), places=2)),
        "article_number": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")))),
        "reviews": draw(st.lists(
            st.fixed_dictionaries({
                "rating": st.integers(min_value=1, max_value=5),
                "comment": st.text(max_size=500, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po"))),
                "user": st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")))
            }),
            max_size=10
        )),
        "images": draw(st.lists(
            st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Po"))),
            max_size=10
        ))
    }


@st.composite
def product_sizes_strategy(draw):
    """Generate valid product sizes data."""
    # Generate 1-9 different sizes (no duplicates)
    selected_sizes = draw(st.lists(
        st.sampled_from(VALID_SIZES),
        min_size=1,
        max_size=9,
        unique=True
    ))
    
    return [
        {
            "size": size,
            "quantity": draw(st.integers(min_value=0, max_value=1000))
        }
        for size in selected_sizes
    ]


class TestProductDataIntegrity:
    """
    Property tests for product data integrity.
    
    **Feature: spoxpro-backend, Property 1: Product Data Integrity**
    **Validates: Requirements 1.1, 1.4**
    """
    
    @given(
        product_data=product_data_strategy(),
        sizes_data=product_sizes_strategy()
    )
    @settings(
        max_examples=20, 
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_product_data_integrity_property(self, product_data, sizes_data):
        """
        **Feature: spoxpro-backend, Property 1: Product Data Integrity**
        
        Property: For any product data with all required fields, storing and retrieving 
        the product should preserve all field values including name, description, 
        type relationships, sizes with quantities, and metadata.
        
        **Validates: Requirements 1.1, 1.4**
        """
        # Create fresh database session for this test
        test_db = create_test_db_session()
        
        try:
            # Create helper data
            helper_data = create_sample_helper_data(test_db)
            
            # Create product with generated data
            product = Product(
                name=product_data["name"],
                description=product_data["description"],
                product_type_id=helper_data["product_type_id"],
                category_id=helper_data["category_id"],
                sport_type_id=helper_data["sport_type_id"],
                material_id=helper_data["material_id"],
                color=product_data["color"],
                gender=product_data["gender"],
                brand=product_data["brand"],
                price=product_data["price"],
                reviews=product_data["reviews"],
                article_number=product_data["article_number"],
                images=product_data["images"],
                product_views=0  # Default value
            )
            
            # Store product
            test_db.add(product)
            test_db.commit()
            test_db.refresh(product)
            
            # Create and store product sizes
            created_sizes = []
            for size_data in sizes_data:
                product_size = ProductSize(
                    product_id=product.id,
                    size=size_data["size"],
                    quantity=size_data["quantity"]
                )
                test_db.add(product_size)
                created_sizes.append(product_size)
            
            test_db.commit()
            
            # Refresh all sizes
            for size in created_sizes:
                test_db.refresh(size)
            
            # Retrieve product from database
            retrieved_product = test_db.query(Product).filter(Product.id == product.id).first()
            
            # Verify product is not None
            assert retrieved_product is not None, "Product should be retrievable after storage"
            
            # Verify all basic fields are preserved exactly
            assert retrieved_product.name == product_data["name"], "Product name should be preserved"
            assert retrieved_product.description == product_data["description"], "Product description should be preserved"
            assert retrieved_product.color == product_data["color"], "Product color should be preserved"
            assert retrieved_product.gender == product_data["gender"], "Product gender should be preserved"
            assert retrieved_product.brand == product_data["brand"], "Product brand should be preserved"
            assert retrieved_product.price == product_data["price"], "Product price should be preserved"
            assert retrieved_product.article_number == product_data["article_number"], "Article number should be preserved"
            assert retrieved_product.product_views == 0, "Product views should be initialized to 0"
            
            # Verify foreign key relationships are maintained
            assert retrieved_product.product_type_id == helper_data["product_type_id"], "Product type relationship should be preserved"
            assert retrieved_product.category_id == helper_data["category_id"], "Category relationship should be preserved"
            assert retrieved_product.sport_type_id == helper_data["sport_type_id"], "Sport type relationship should be preserved"
            assert retrieved_product.material_id == helper_data["material_id"], "Material relationship should be preserved"
            
            # Verify JSON fields preserve structure and content
            assert retrieved_product.reviews == product_data["reviews"], "Reviews JSON should be preserved exactly"
            assert retrieved_product.images == product_data["images"], "Images JSON should be preserved exactly"
            
            # Verify metadata fields are set
            assert retrieved_product.created_date is not None, "Created date should be set"
            assert retrieved_product.last_updated_date is not None, "Last updated date should be set"
            assert isinstance(retrieved_product.created_date, datetime), "Created date should be datetime"
            assert isinstance(retrieved_product.last_updated_date, datetime), "Last updated date should be datetime"
            
            # Verify ProductSize data integrity
            retrieved_sizes = test_db.query(ProductSize).filter(ProductSize.product_id == product.id).all()
            
            # Check that all sizes were stored
            assert len(retrieved_sizes) == len(sizes_data), f"Expected {len(sizes_data)} sizes, got {len(retrieved_sizes)}"
            
            # Create lookup for easier verification
            retrieved_sizes_dict = {size.size: size.quantity for size in retrieved_sizes}
            expected_sizes_dict = {size_data["size"]: size_data["quantity"] for size_data in sizes_data}
            
            # Verify each size and quantity is preserved
            for size, expected_quantity in expected_sizes_dict.items():
                assert size in retrieved_sizes_dict, f"Size {size} should be preserved"
                assert retrieved_sizes_dict[size] == expected_quantity, f"Quantity for size {size} should be preserved"
            
            # Verify foreign key relationship in sizes
            for retrieved_size in retrieved_sizes:
                assert retrieved_size.product_id == product.id, "ProductSize should reference correct product"
            
            # Verify relationship navigation works
            assert retrieved_product.product_type is not None, "Product type relationship should be navigable"
            assert retrieved_product.category is not None, "Category relationship should be navigable"
            assert retrieved_product.sport_type is not None, "Sport type relationship should be navigable"
            assert retrieved_product.material is not None, "Material relationship should be navigable"
            
            # Verify sizes relationship
            product_sizes_via_relationship = retrieved_product.sizes
            assert len(product_sizes_via_relationship) == len(sizes_data), "Sizes relationship should return all sizes"
            
            # Test edge cases for JSON fields
            if not product_data["reviews"]:  # Empty list
                assert retrieved_product.reviews == [], "Empty reviews list should be preserved"
            
            if not product_data["images"]:  # Empty list
                assert retrieved_product.images == [], "Empty images list should be preserved"
        
        finally:
            # Clean up
            test_db.close()
    
    
    def test_product_data_integrity_with_empty_json_fields(self, test_db, sample_helper_data):
        """
        Test product data integrity with empty JSON fields.
        
        **Feature: spoxpro-backend, Property 1: Product Data Integrity**
        **Validates: Requirements 1.1, 1.4**
        """
        # Create product with empty JSON fields
        product = Product(
            name="Test Product",
            description="Test Description",
            product_type_id=sample_helper_data["product_type_id"],
            category_id=sample_helper_data["category_id"],
            sport_type_id=sample_helper_data["sport_type_id"],
            material_id=sample_helper_data["material_id"],
            color="Red",
            gender="unisex",
            brand="spoXpro",
            price=Decimal("29.99"),
            reviews=[],  # Empty list
            article_number="TEST001",
            images=[],  # Empty list
        )
        
        # Store and retrieve
        test_db.add(product)
        test_db.commit()
        test_db.refresh(product)
        
        retrieved_product = test_db.query(Product).filter(Product.id == product.id).first()
        
        # Verify empty JSON fields are preserved
        assert retrieved_product.reviews == [], "Empty reviews should be preserved as empty list"
        assert retrieved_product.images == [], "Empty images should be preserved as empty list"
    
    
    def test_product_data_integrity_with_complex_json_structures(self, test_db, sample_helper_data):
        """
        Test product data integrity with complex JSON structures.
        
        **Feature: spoxpro-backend, Property 1: Product Data Integrity**
        **Validates: Requirements 1.1, 1.4**
        """
        # Create complex JSON data
        complex_reviews = [
            {
                "rating": 5,
                "comment": "Excellent product with great quality!",
                "user": "john_doe",
                "date": "2024-01-15",
                "verified_purchase": True,
                "helpful_votes": 12
            },
            {
                "rating": 4,
                "comment": "Good value for money",
                "user": "jane_smith",
                "date": "2024-01-10",
                "verified_purchase": False,
                "helpful_votes": 3
            }
        ]
        
        complex_images = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "https://example.com/image3_large.jpg"
        ]
        
        product = Product(
            name="Complex Test Product",
            description="Product with complex JSON data",
            product_type_id=sample_helper_data["product_type_id"],
            category_id=sample_helper_data["category_id"],
            sport_type_id=sample_helper_data["sport_type_id"],
            material_id=sample_helper_data["material_id"],
            color="Blue",
            gender="male",
            brand="spoXpro",
            price=Decimal("59.99"),
            reviews=complex_reviews,
            article_number="COMPLEX001",
            images=complex_images,
        )
        
        # Store and retrieve
        test_db.add(product)
        test_db.commit()
        test_db.refresh(product)
        
        retrieved_product = test_db.query(Product).filter(Product.id == product.id).first()
        
        # Verify complex JSON structures are preserved exactly
        assert retrieved_product.reviews == complex_reviews, "Complex reviews structure should be preserved"
        assert retrieved_product.images == complex_images, "Complex images structure should be preserved"
        
        # Verify nested data in reviews
        assert len(retrieved_product.reviews) == 2, "Should have 2 reviews"
        assert retrieved_product.reviews[0]["rating"] == 5, "First review rating should be preserved"
        assert retrieved_product.reviews[0]["verified_purchase"] is True, "Boolean values should be preserved"
        assert retrieved_product.reviews[1]["helpful_votes"] == 3, "Nested integer values should be preserved"


    def test_product_size_combinations_integrity(self, test_db, sample_helper_data):
        """
        Test product data integrity with different size combinations.
        
        **Feature: spoxpro-backend, Property 1: Product Data Integrity**
        **Validates: Requirements 1.1, 1.4**
        """
        # Test with all possible sizes
        product = Product(
            name="All Sizes Product",
            description="Product with all size options",
            product_type_id=sample_helper_data["product_type_id"],
            category_id=sample_helper_data["category_id"],
            sport_type_id=sample_helper_data["sport_type_id"],
            material_id=sample_helper_data["material_id"],
            color="Green",
            gender="unisex",
            brand="spoXpro",
            price=Decimal("39.99"),
            reviews=[],
            article_number="ALLSIZES001",
            images=["image1.jpg"],
        )
        
        test_db.add(product)
        test_db.commit()
        test_db.refresh(product)
        
        # Add all possible sizes with different quantities
        all_sizes_data = []
        for i, size in enumerate(VALID_SIZES):
            quantity = (i + 1) * 10  # Different quantity for each size
            product_size = ProductSize(
                product_id=product.id,
                size=size,
                quantity=quantity
            )
            test_db.add(product_size)
            all_sizes_data.append({"size": size, "quantity": quantity})
        
        test_db.commit()
        
        # Retrieve and verify
        retrieved_product = test_db.query(Product).filter(Product.id == product.id).first()
        retrieved_sizes = test_db.query(ProductSize).filter(ProductSize.product_id == product.id).all()
        
        # Verify all sizes are preserved
        assert len(retrieved_sizes) == len(VALID_SIZES), f"Should have all {len(VALID_SIZES)} sizes"
        
        retrieved_sizes_dict = {size.size: size.quantity for size in retrieved_sizes}
        
        for size_data in all_sizes_data:
            size = size_data["size"]
            expected_quantity = size_data["quantity"]
            assert size in retrieved_sizes_dict, f"Size {size} should be present"
            assert retrieved_sizes_dict[size] == expected_quantity, f"Quantity for {size} should be {expected_quantity}"
