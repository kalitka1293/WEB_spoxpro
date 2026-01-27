"""
Property-based tests for product search filtering functionality.

**Feature: spoxpro-backend, Property 2: Product Search Filtering**
**Validates: Requirements 1.2**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from decimal import Decimal
from typing import List, Dict, Any, Optional
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.services.product_service import ProductService
from backend.db.models.product import Product, ProductSize, ProductType, Category, SportType, Material
from backend.config.database import Base


# Valid clothing sizes as per requirements
VALID_SIZES = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "XXXXL"]
VALID_GENDERS = ["male", "female", "unisex"]
VALID_COLORS = ["Red", "Blue", "Green", "Black", "White", "Yellow", "Purple", "Orange", "Pink", "Gray"]


def create_test_db_session():
    """Create a test database session for property tests."""
    # Use in-memory SQLite database for faster tests
    test_engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )
    
    # Enable foreign key constraints for SQLite
    from sqlalchemy import event
    
    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create test session
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    return TestSessionLocal()


def create_sample_helper_data(db):
    """Create sample helper table data for property tests."""
    # Create helper table records with unique names to avoid conflicts
    unique_suffix = str(uuid.uuid4())[:8]
    
    product_type = ProductType(name=f"T-Shirt-{unique_suffix}")
    category = Category(name=f"Men's Clothing-{unique_suffix}")
    sport_type = SportType(name=f"Running-{unique_suffix}")
    material = Material(name=f"Cotton-{unique_suffix}")
    
    db.add_all([product_type, category, sport_type, material])
    db.commit()
    
    return {
        "product_type": product_type,
        "category": category,
        "sport_type": sport_type,
        "material": material
    }


# Hypothesis strategies for generating test data
@st.composite
def product_data_strategy(draw):
    """Generate valid product data for testing."""
    unique_id = str(uuid.uuid4())[:8]
    
    return {
        'name': draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs')))),
        'description': draw(st.text(min_size=1, max_size=500, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs')))),
        'color': draw(st.sampled_from(VALID_COLORS)),
        'gender': draw(st.sampled_from(VALID_GENDERS)),
        'brand': draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        'price': draw(st.decimals(min_value=Decimal('0.01'), max_value=Decimal('999.99'), places=2)),
        'article_number': f'ART-{unique_id}',
        'images': draw(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5)),
        'reviews': [],
        'sizes': draw(st.lists(
            st.fixed_dictionaries({
                'size': st.sampled_from(VALID_SIZES),
                'quantity': st.integers(min_value=0, max_value=100)
            }),
            min_size=1,
            max_size=5,
            unique_by=lambda x: x['size']
        ))
    }


@st.composite
def filter_criteria_strategy(draw, available_values=None):
    """Generate filter criteria for testing."""
    filters = {}
    
    # Randomly include each filter type
    if draw(st.booleans()) and available_values and 'categories' in available_values:
        filters['category'] = draw(st.sampled_from(available_values['categories']))
    
    if draw(st.booleans()) and available_values and 'product_types' in available_values:
        filters['product_type'] = draw(st.sampled_from(available_values['product_types']))
    
    if draw(st.booleans()) and available_values and 'sport_types' in available_values:
        filters['sport_type'] = draw(st.sampled_from(available_values['sport_types']))
    
    if draw(st.booleans()) and available_values and 'materials' in available_values:
        filters['material'] = draw(st.sampled_from(available_values['materials']))
    
    if draw(st.booleans()):
        filters['color'] = draw(st.sampled_from(VALID_COLORS))
    
    if draw(st.booleans()):
        filters['gender'] = draw(st.sampled_from(VALID_GENDERS))
    
    if draw(st.booleans()):
        filters['size'] = draw(st.sampled_from(VALID_SIZES))
    
    # Price range filters
    if draw(st.booleans()):
        min_price = draw(st.decimals(min_value=Decimal('0.01'), max_value=Decimal('500.00'), places=2))
        max_price = draw(st.decimals(min_value=min_price, max_value=Decimal('999.99'), places=2))
        filters['min_price'] = min_price
        filters['max_price'] = max_price
    
    return filters


def create_test_products(db, product_service, helper_data, products_data):
    """Create test products in the database."""
    created_products = []
    
    for product_data in products_data:
        # Add helper table IDs
        full_product_data = {
            **product_data,
            'product_type_id': helper_data['product_type'].id,
            'category_id': helper_data['category'].id,
            'sport_type_id': helper_data['sport_type'].id,
            'material_id': helper_data['material'].id
        }
        
        product = product_service.create_product(full_product_data)
        if product:
            created_products.append(product)
    
    return created_products


def product_matches_filters(product, filters, helper_data):
    """Check if a product matches the given filter criteria."""
    # Category filter
    if 'category' in filters:
        if isinstance(filters['category'], str):
            if helper_data['category'].name != filters['category']:
                return False
        else:
            if product.category_id != filters['category']:
                return False
    
    # Product type filter
    if 'product_type' in filters:
        if isinstance(filters['product_type'], str):
            if helper_data['product_type'].name != filters['product_type']:
                return False
        else:
            if product.product_type_id != filters['product_type']:
                return False
    
    # Sport type filter
    if 'sport_type' in filters:
        if isinstance(filters['sport_type'], str):
            if helper_data['sport_type'].name != filters['sport_type']:
                return False
        else:
            if product.sport_type_id != filters['sport_type']:
                return False
    
    # Material filter
    if 'material' in filters:
        if isinstance(filters['material'], str):
            if helper_data['material'].name != filters['material']:
                return False
        else:
            if product.material_id != filters['material']:
                return False
    
    # Color filter
    if 'color' in filters:
        if filters['color'].lower() not in product.color.lower():
            return False
    
    # Gender filter
    if 'gender' in filters:
        if product.gender != filters['gender']:
            return False
    
    # Price range filters
    if 'min_price' in filters:
        if product.price < filters['min_price']:
            return False
    
    if 'max_price' in filters:
        if product.price > filters['max_price']:
            return False
    
    # Size availability filter
    if 'size' in filters:
        size_available = False
        for size in product.sizes:
            if size.size == filters['size'] and size.quantity > 0:
                size_available = True
                break
        if not size_available:
            return False
    
    return True


class TestProductSearchFilteringProperties:
    """Property-based tests for product search filtering."""
    
    @given(
        products_data=st.lists(product_data_strategy(), min_size=1, max_size=10),
        filters=filter_criteria_strategy()
    )
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large]
    )
    def test_product_filtering_correctness(self, products_data, filters):
        """
        **Feature: spoxpro-backend, Property 2: Product Search Filtering**
        **Validates: Requirements 1.2**
        
        Property: For any set of products and any combination of valid filter criteria 
        (type, category, sport, color, gender, size availability, price range), 
        the search results should contain only products that match all specified filters.
        """
        # Create test database session
        db = create_test_db_session()
        
        try:
            # Create helper data
            helper_data = create_sample_helper_data(db)
            product_service = ProductService(db)
            
            # Create test products
            created_products = create_test_products(db, product_service, helper_data, products_data)
            
            # Skip test if no products were created successfully
            assume(len(created_products) > 0)
            
            # Apply filters and get results
            filtered_products = product_service.get_products_filtered(filters)
            
            # Verify that all returned products match the filter criteria
            for product in filtered_products:
                assert product_matches_filters(product, filters, helper_data), \
                    f"Product {product.id} ({product.name}) does not match filters {filters}"
            
            # Verify that no matching products were excluded
            # (Check that all products that should match are in the results)
            expected_products = []
            for product in created_products:
                if product_matches_filters(product, filters, helper_data):
                    expected_products.append(product)
            
            result_ids = {p.id for p in filtered_products}
            expected_ids = {p.id for p in expected_products}
            
            # All expected products should be in results
            missing_products = expected_ids - result_ids
            assert len(missing_products) == 0, \
                f"Expected products {missing_products} were not returned by filter"
            
            # No unexpected products should be in results
            unexpected_products = result_ids - expected_ids
            assert len(unexpected_products) == 0, \
                f"Unexpected products {unexpected_products} were returned by filter"
        
        finally:
            db.close()
    
    @given(
        products_data=st.lists(product_data_strategy(), min_size=5, max_size=15)
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large]
    )
    def test_empty_filters_return_all_products(self, products_data):
        """
        Property: When no filters are applied, all products should be returned.
        """
        # Create test database session
        db = create_test_db_session()
        
        try:
            # Create helper data
            helper_data = create_sample_helper_data(db)
            product_service = ProductService(db)
            
            # Create test products
            created_products = create_test_products(db, product_service, helper_data, products_data)
            
            # Skip test if no products were created successfully
            assume(len(created_products) > 0)
            
            # Get all products with no filters
            all_products = product_service.get_products_filtered({})
            
            # Should return all created products
            result_ids = {p.id for p in all_products}
            expected_ids = {p.id for p in created_products}
            
            assert result_ids == expected_ids, \
                f"Empty filter should return all products. Expected {len(expected_ids)}, got {len(result_ids)}"
        
        finally:
            db.close()
    
    @given(
        products_data=st.lists(product_data_strategy(), min_size=3, max_size=8),
        size_filter=st.sampled_from(VALID_SIZES)
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large]
    )
    def test_size_availability_filtering(self, products_data, size_filter):
        """
        Property: Size filtering should only return products that have the specified size 
        with quantity > 0.
        """
        # Create test database session
        db = create_test_db_session()
        
        try:
            # Create helper data
            helper_data = create_sample_helper_data(db)
            product_service = ProductService(db)
            
            # Create test products
            created_products = create_test_products(db, product_service, helper_data, products_data)
            
            # Skip test if no products were created successfully
            assume(len(created_products) > 0)
            
            # Filter by size
            filtered_products = product_service.get_products_filtered({'size': size_filter})
            
            # Verify all returned products have the specified size with quantity > 0
            for product in filtered_products:
                has_size_available = False
                for size in product.sizes:
                    if size.size == size_filter and size.quantity > 0:
                        has_size_available = True
                        break
                
                assert has_size_available, \
                    f"Product {product.id} returned for size {size_filter} but doesn't have it available"
        
        finally:
            db.close()
