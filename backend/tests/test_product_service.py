"""
Tests for ProductService functionality.

This test suite verifies all CRUD operations, filtering, search, inventory management,
and view count functionality of the ProductService.
"""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.db.main import get_db_session_context, init_database
from backend.db.services.product_service import ProductService
from backend.db.models.product import (
    Product, ProductSize, ProductType, Category, SportType, Material
)


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    # Initialize database for testing
    init_database()
    
    with get_db_session_context() as db:
        # Clean up any existing data before each test
        db.execute(text("DELETE FROM product_sizes"))
        db.execute(text("DELETE FROM products"))
        db.execute(text("DELETE FROM categories"))
        db.execute(text("DELETE FROM product_types"))
        db.execute(text("DELETE FROM sport_types"))
        db.execute(text("DELETE FROM materials"))
        db.commit()
        yield db


@pytest.fixture
def product_service(db_session):
    """Create a ProductService instance."""
    return ProductService(db_session)


@pytest.fixture
def sample_helper_data(product_service):
    """Create sample helper table data."""
    import uuid
    
    # Create unique helper table entries to avoid conflicts
    unique_suffix = str(uuid.uuid4())[:8]
    
    category = product_service.create_category(f"Men's Clothing {unique_suffix}")
    product_type = product_service.create_product_type(f"T-Shirt {unique_suffix}")
    sport_type = product_service.create_sport_type(f"Running {unique_suffix}")
    material = product_service.create_material(f"Cotton {unique_suffix}")
    
    # If creation fails, try to get existing ones
    if not category:
        categories = product_service.get_all_categories()
        category = categories[0] if categories else None
    if not product_type:
        types = product_service.get_all_product_types()
        product_type = types[0] if types else None
    if not sport_type:
        sports = product_service.get_all_sport_types()
        sport_type = sports[0] if sports else None
    if not material:
        materials = product_service.get_all_materials()
        material = materials[0] if materials else None
    
    return {
        'category_id': category.id,
        'product_type_id': product_type.id,
        'sport_type_id': sport_type.id,
        'material_id': material.id
    }


@pytest.fixture
def sample_product_data(sample_helper_data):
    """Create sample product data."""
    import uuid
    unique_suffix = str(uuid.uuid4())[:8]
    
    return {
        'name': 'Test Running T-Shirt',
        'description': 'A comfortable running t-shirt for men',
        'product_type_id': sample_helper_data['product_type_id'],
        'category_id': sample_helper_data['category_id'],
        'sport_type_id': sample_helper_data['sport_type_id'],
        'material_id': sample_helper_data['material_id'],
        'color': 'Blue',
        'gender': 'male',
        'brand': 'spoXpro',
        'price': Decimal('29.99'),
        'article_number': f'TSH-RUN-{unique_suffix}',
        'images': ['image1.jpg', 'image2.jpg'],
        'reviews': [],
        'sizes': [
            {'size': 'S', 'quantity': 10},
            {'size': 'M', 'quantity': 15},
            {'size': 'L', 'quantity': 8},
            {'size': 'XL', 'quantity': 5}
        ]
    }


class TestProductCRUD:
    """Test CRUD operations for products."""
    
    def test_create_product_success(self, product_service, sample_product_data):
        """Test successful product creation."""
        product = product_service.create_product(sample_product_data)
        
        assert product is not None
        assert product.name == sample_product_data['name']
        assert product.description == sample_product_data['description']
        assert product.color == sample_product_data['color']
        assert product.gender == sample_product_data['gender']
        assert product.price == sample_product_data['price']
        assert product.article_number == sample_product_data['article_number']
        assert len(product.sizes) == 4
        
        # Check sizes were created correctly
        size_dict = {size.size: size.quantity for size in product.sizes}
        assert size_dict['S'] == 10
        assert size_dict['M'] == 15
        assert size_dict['L'] == 8
        assert size_dict['XL'] == 5
    
    def test_create_product_duplicate_article_number(self, product_service, sample_product_data):
        """Test product creation with duplicate article number fails."""
        # Create first product
        product1 = product_service.create_product(sample_product_data)
        assert product1 is not None
        
        # Try to create second product with same article number
        sample_product_data['name'] = 'Different Name'
        # Keep the same article number to test duplicate constraint
        product2 = product_service.create_product(sample_product_data)
        assert product2 is None  # Should fail due to unique constraint
    
    def test_get_product_by_id(self, product_service, sample_product_data):
        """Test retrieving product by ID."""
        created_product = product_service.create_product(sample_product_data)
        assert created_product is not None
        
        retrieved_product = product_service.get_product_by_id(created_product.id)
        assert retrieved_product is not None
        assert retrieved_product.id == created_product.id
        assert retrieved_product.name == sample_product_data['name']
        assert len(retrieved_product.sizes) == 4
    
    def test_get_product_by_id_not_found(self, product_service):
        """Test retrieving non-existent product returns None."""
        product = product_service.get_product_by_id(99999)
        assert product is None
    
    def test_get_product_by_article_number(self, product_service, sample_product_data):
        """Test retrieving product by article number."""
        created_product = product_service.create_product(sample_product_data)
        assert created_product is not None
        
        retrieved_product = product_service.get_product_by_article_number(sample_product_data['article_number'])
        assert retrieved_product is not None
        assert retrieved_product.id == created_product.id
        assert retrieved_product.article_number == sample_product_data['article_number']
    
    def test_update_product(self, product_service, sample_product_data):
        """Test updating product information."""
        product = product_service.create_product(sample_product_data)
        assert product is not None
        
        updates = {
            'name': 'Updated T-Shirt Name',
            'price': Decimal('34.99'),
            'color': 'Red'
        }
        
        updated_product = product_service.update_product(product.id, updates)
        assert updated_product is not None
        assert updated_product.name == 'Updated T-Shirt Name'
        assert updated_product.price == Decimal('34.99')
        assert updated_product.color == 'Red'
    
    def test_update_product_with_sizes(self, product_service, sample_product_data):
        """Test updating product with new sizes."""
        product = product_service.create_product(sample_product_data)
        assert product is not None
        
        new_sizes = [
            {'size': 'XS', 'quantity': 5},
            {'size': 'S', 'quantity': 20},
            {'size': 'M', 'quantity': 25}
        ]
        
        updated_product = product_service.update_product(product.id, {'sizes': new_sizes})
        assert updated_product is not None
        assert len(updated_product.sizes) == 3
        
        size_dict = {size.size: size.quantity for size in updated_product.sizes}
        assert size_dict['XS'] == 5
        assert size_dict['S'] == 20
        assert size_dict['M'] == 25
    
    def test_delete_product(self, product_service, sample_product_data):
        """Test deleting a product."""
        product = product_service.create_product(sample_product_data)
        assert product is not None
        
        success = product_service.delete_product(product.id)
        assert success is True
        
        # Verify product is deleted
        deleted_product = product_service.get_product_by_id(product.id)
        assert deleted_product is None


class TestProductFiltering:
    """Test product filtering and search functionality."""
    
    def test_get_products_no_filters(self, product_service, sample_helper_data):
        """Test getting all products without filters."""
        # Create multiple products
        for i in range(3):
            product_data = {
                'name': f'Test Product {i}',
                'description': f'Description {i}',
                'product_type_id': sample_helper_data['product_type_id'],
                'category_id': sample_helper_data['category_id'],
                'sport_type_id': sample_helper_data['sport_type_id'],
                'material_id': sample_helper_data['material_id'],
                'color': 'Blue',
                'gender': 'male',
                'price': Decimal('29.99'),
                'article_number': f'TSH-FILTER-{i:03d}',
                'sizes': [{'size': 'M', 'quantity': 10}]
            }
            product_service.create_product(product_data)
        
        products = product_service.get_products_filtered()
        assert len(products) == 3
    
    def test_filter_by_color(self, product_service, sample_helper_data):
        """Test filtering products by color."""
        # Create products with different colors
        colors = ['Red', 'Blue', 'Green']
        for i, color in enumerate(colors):
            product_data = {
                'name': f'Test Product {i}',
                'description': f'Description {i}',
                'product_type_id': sample_helper_data['product_type_id'],
                'category_id': sample_helper_data['category_id'],
                'sport_type_id': sample_helper_data['sport_type_id'],
                'material_id': sample_helper_data['material_id'],
                'color': color,
                'gender': 'male',
                'price': Decimal('29.99'),
                'article_number': f'TSH-COLOR-{i:03d}',
                'sizes': [{'size': 'M', 'quantity': 10}]
            }
            product_service.create_product(product_data)
        
        # Filter by blue color
        blue_products = product_service.get_products_filtered({'color': 'Blue'})
        assert len(blue_products) == 1
        assert blue_products[0].color == 'Blue'
    
    def test_filter_by_price_range(self, product_service, sample_helper_data):
        """Test filtering products by price range."""
        # Create products with different prices
        prices = [Decimal('19.99'), Decimal('29.99'), Decimal('39.99')]
        for i, price in enumerate(prices):
            product_data = {
                'name': f'Test Product {i}',
                'description': f'Description {i}',
                'product_type_id': sample_helper_data['product_type_id'],
                'category_id': sample_helper_data['category_id'],
                'sport_type_id': sample_helper_data['sport_type_id'],
                'material_id': sample_helper_data['material_id'],
                'color': 'Blue',
                'gender': 'male',
                'price': price,
                'article_number': f'TSH-PRICE-{i:03d}',
                'sizes': [{'size': 'M', 'quantity': 10}]
            }
            product_service.create_product(product_data)
        
        # Filter by price range
        filtered_products = product_service.get_products_filtered({
            'min_price': Decimal('25.00'),
            'max_price': Decimal('35.00')
        })
        assert len(filtered_products) == 1
        assert filtered_products[0].price == Decimal('29.99')
    
    def test_filter_by_size_availability(self, product_service, sample_helper_data):
        """Test filtering products by size availability."""
        # Create products with different size availability
        product_data_1 = {
            'name': 'Product with S',
            'description': 'Has size S',
            'product_type_id': sample_helper_data['product_type_id'],
            'category_id': sample_helper_data['category_id'],
            'sport_type_id': sample_helper_data['sport_type_id'],
            'material_id': sample_helper_data['material_id'],
            'color': 'Blue',
            'gender': 'male',
            'price': Decimal('29.99'),
            'article_number': 'TSH-SIZE-001',
            'sizes': [{'size': 'S', 'quantity': 10}, {'size': 'M', 'quantity': 0}]
        }
        
        product_data_2 = {
            'name': 'Product with M',
            'description': 'Has size M',
            'product_type_id': sample_helper_data['product_type_id'],
            'category_id': sample_helper_data['category_id'],
            'sport_type_id': sample_helper_data['sport_type_id'],
            'material_id': sample_helper_data['material_id'],
            'color': 'Blue',
            'gender': 'male',
            'price': Decimal('29.99'),
            'article_number': 'TSH-SIZE-002',
            'sizes': [{'size': 'S', 'quantity': 0}, {'size': 'M', 'quantity': 10}]
        }
        
        product_service.create_product(product_data_1)
        product_service.create_product(product_data_2)
        
        # Filter by size S availability
        s_products = product_service.get_products_filtered({'size': 'S'})
        assert len(s_products) == 1
        assert s_products[0].name == 'Product with S'
        
        # Filter by size M availability
        m_products = product_service.get_products_filtered({'size': 'M'})
        assert len(m_products) == 1
        assert m_products[0].name == 'Product with M'
    
    def test_search_products(self, product_service, sample_helper_data):
        """Test product search functionality."""
        # Create products with different names and descriptions
        products_data = [
            {
                'name': 'Running Shoes',
                'description': 'Great for jogging and marathons',
                'article_number': 'SHO-SEARCH-001'
            },
            {
                'name': 'Basketball Jersey',
                'description': 'Perfect for basketball games',
                'article_number': 'JER-SEARCH-001'
            },
            {
                'name': 'Tennis Racket',
                'description': 'Professional tennis equipment',
                'article_number': 'RAC-SEARCH-001'
            }
        ]
        
        for product_data in products_data:
            full_data = {
                **product_data,
                'product_type_id': sample_helper_data['product_type_id'],
                'category_id': sample_helper_data['category_id'],
                'sport_type_id': sample_helper_data['sport_type_id'],
                'material_id': sample_helper_data['material_id'],
                'color': 'Blue',
                'gender': 'male',
                'price': Decimal('29.99'),
                'sizes': [{'size': 'M', 'quantity': 10}]
            }
            product_service.create_product(full_data)
        
        # Search by name
        running_products = product_service.search_products('Running')
        assert len(running_products) == 1
        assert 'Running' in running_products[0].name
        
        # Search by description
        basketball_products = product_service.search_products('basketball')
        assert len(basketball_products) == 1
        assert 'Basketball' in basketball_products[0].name


class TestInventoryManagement:
    """Test inventory management functionality."""
    
    def test_get_product_inventory_all_sizes(self, product_service, sample_product_data):
        """Test getting inventory for all sizes."""
        product = product_service.create_product(sample_product_data)
        assert product is not None
        
        inventory = product_service.get_product_inventory(product.id)
        assert isinstance(inventory, dict)
        assert inventory['S'] == 10
        assert inventory['M'] == 15
        assert inventory['L'] == 8
        assert inventory['XL'] == 5
    
    def test_get_product_inventory_specific_size(self, product_service, sample_product_data):
        """Test getting inventory for specific size."""
        product = product_service.create_product(sample_product_data)
        assert product is not None
        
        m_quantity = product_service.get_product_inventory(product.id, 'M')
        assert m_quantity == 15
        
        xl_quantity = product_service.get_product_inventory(product.id, 'XL')
        assert xl_quantity == 5
        
        # Test non-existent size
        xxl_quantity = product_service.get_product_inventory(product.id, 'XXL')
        assert xxl_quantity == 0
    
    def test_update_product_inventory_increase(self, product_service, sample_product_data):
        """Test increasing product inventory."""
        product = product_service.create_product(sample_product_data)
        assert product is not None
        
        # Increase M size inventory by 5
        success = product_service.update_product_inventory(product.id, 'M', 5)
        assert success is True
        
        # Check new quantity
        new_quantity = product_service.get_product_inventory(product.id, 'M')
        assert new_quantity == 20  # 15 + 5
    
    def test_update_product_inventory_decrease(self, product_service, sample_product_data):
        """Test decreasing product inventory."""
        product = product_service.create_product(sample_product_data)
        assert product is not None
        
        # Decrease M size inventory by 3
        success = product_service.update_product_inventory(product.id, 'M', -3)
        assert success is True
        
        # Check new quantity
        new_quantity = product_service.get_product_inventory(product.id, 'M')
        assert new_quantity == 12  # 15 - 3
    
    def test_update_product_inventory_prevent_negative(self, product_service, sample_product_data):
        """Test preventing negative inventory."""
        product = product_service.create_product(sample_product_data)
        assert product is not None
        
        # Try to decrease inventory below zero
        success = product_service.update_product_inventory(product.id, 'M', -20)
        assert success is False
        
        # Check quantity unchanged
        quantity = product_service.get_product_inventory(product.id, 'M')
        assert quantity == 15  # Original quantity
    
    def test_check_inventory_availability(self, product_service, sample_product_data):
        """Test checking inventory availability."""
        product = product_service.create_product(sample_product_data)
        assert product is not None
        
        # Check available quantity
        available = product_service.check_inventory_availability(product.id, 'M', 10)
        assert available is True
        
        # Check exact quantity
        available = product_service.check_inventory_availability(product.id, 'M', 15)
        assert available is True
        
        # Check more than available
        available = product_service.check_inventory_availability(product.id, 'M', 20)
        assert available is False
        
        # Check non-existent size
        available = product_service.check_inventory_availability(product.id, 'XXL', 1)
        assert available is False


class TestProductViews:
    """Test product view count functionality."""
    
    def test_increment_product_views(self, product_service, sample_product_data):
        """Test incrementing product view count."""
        product = product_service.create_product(sample_product_data)
        assert product is not None
        assert product.product_views == 0
        
        # Increment views
        success = product_service.increment_product_views(product.id)
        assert success is True
        
        # Check updated count
        updated_product = product_service.get_product_by_id(product.id)
        assert updated_product.product_views == 1
        
        # Increment again
        success = product_service.increment_product_views(product.id)
        assert success is True
        
        updated_product = product_service.get_product_by_id(product.id)
        assert updated_product.product_views == 2
    
    def test_increment_views_nonexistent_product(self, product_service):
        """Test incrementing views for non-existent product."""
        success = product_service.increment_product_views(99999)
        assert success is False


class TestHelperTables:
    """Test helper table operations."""
    
    def test_create_and_get_categories(self, product_service):
        """Test creating and retrieving categories."""
        import uuid
        unique_suffix = str(uuid.uuid4())[:8]
        
        # Create categories with unique names
        cat1 = product_service.create_category(f"Men's Clothing {unique_suffix}")
        cat2 = product_service.create_category(f"Women's Clothing {unique_suffix}")
        
        assert cat1 is not None
        assert cat2 is not None
        assert f"Men's Clothing {unique_suffix}" in cat1.name
        assert f"Women's Clothing {unique_suffix}" in cat2.name
        
        # Get all categories
        categories = product_service.get_all_categories()
        assert len(categories) >= 2
        category_names = [cat.name for cat in categories]
        assert cat1.name in category_names
        assert cat2.name in category_names
    
    def test_create_duplicate_category(self, product_service):
        """Test creating duplicate category fails."""
        import uuid
        unique_name = f"Test Category {str(uuid.uuid4())[:8]}"
        
        cat1 = product_service.create_category(unique_name)
        assert cat1 is not None
        
        cat2 = product_service.create_category(unique_name)
        assert cat2 is None  # Should fail due to unique constraint
    
    def test_create_and_get_product_types(self, product_service):
        """Test creating and retrieving product types."""
        import uuid
        unique_suffix = str(uuid.uuid4())[:8]
        
        type1 = product_service.create_product_type(f"T-Shirt {unique_suffix}")
        type2 = product_service.create_product_type(f"Shorts {unique_suffix}")
        
        assert type1 is not None
        assert type2 is not None
        
        types = product_service.get_all_product_types()
        assert len(types) >= 2
        type_names = [t.name for t in types]
        assert type1.name in type_names
        assert type2.name in type_names
    
    def test_create_and_get_sport_types(self, product_service):
        """Test creating and retrieving sport types."""
        import uuid
        unique_suffix = str(uuid.uuid4())[:8]
        
        sport1 = product_service.create_sport_type(f"Running {unique_suffix}")
        sport2 = product_service.create_sport_type(f"Basketball {unique_suffix}")
        
        assert sport1 is not None
        assert sport2 is not None
        
        sports = product_service.get_all_sport_types()
        assert len(sports) >= 2
        sport_names = [s.name for s in sports]
        assert sport1.name in sport_names
        assert sport2.name in sport_names
    
    def test_create_and_get_materials(self, product_service):
        """Test creating and retrieving materials."""
        import uuid
        unique_suffix = str(uuid.uuid4())[:8]
        
        mat1 = product_service.create_material(f"Cotton {unique_suffix}")
        mat2 = product_service.create_material(f"Polyester {unique_suffix}")
        
        assert mat1 is not None
        assert mat2 is not None
        
        materials = product_service.get_all_materials()
        assert len(materials) >= 2
        material_names = [m.name for m in materials]
        assert mat1.name in material_names
        assert mat2.name in material_names


class TestUtilityMethods:
    """Test utility methods."""
    
    def test_get_product_count(self, product_service, sample_helper_data):
        """Test getting product count."""
        # Initially no products
        count = product_service.get_product_count()
        initial_count = count
        
        # Create some products
        for i in range(3):
            product_data = {
                'name': f'Test Product {i}',
                'description': f'Description {i}',
                'product_type_id': sample_helper_data['product_type_id'],
                'category_id': sample_helper_data['category_id'],
                'sport_type_id': sample_helper_data['sport_type_id'],
                'material_id': sample_helper_data['material_id'],
                'color': 'Blue',
                'gender': 'male',
                'price': Decimal('29.99'),
                'article_number': f'TSH-COUNT-{i:03d}',
                'sizes': [{'size': 'M', 'quantity': 10}]
            }
            product_service.create_product(product_data)
        
        count = product_service.get_product_count()
        assert count == initial_count + 3
    
    def test_get_available_sizes_for_product(self, product_service, sample_product_data):
        """Test getting available sizes for a product."""
        # Modify sample data to have some sizes with zero quantity
        sample_product_data['sizes'] = [
            {'size': 'S', 'quantity': 10},
            {'size': 'M', 'quantity': 0},  # No stock
            {'size': 'L', 'quantity': 5},
            {'size': 'XL', 'quantity': 0}  # No stock
        ]
        
        product = product_service.create_product(sample_product_data)
        assert product is not None
        
        available_sizes = product_service.get_available_sizes_for_product(product.id)
        assert len(available_sizes) == 2
        assert 'S' in available_sizes
        assert 'L' in available_sizes
        assert 'M' not in available_sizes
        assert 'XL' not in available_sizes
    
    def test_get_products_by_ids(self, product_service, sample_helper_data):
        """Test getting multiple products by IDs."""
        # Create multiple products
        product_ids = []
        for i in range(3):
            product_data = {
                'name': f'Test Product {i}',
                'description': f'Description {i}',
                'product_type_id': sample_helper_data['product_type_id'],
                'category_id': sample_helper_data['category_id'],
                'sport_type_id': sample_helper_data['sport_type_id'],
                'material_id': sample_helper_data['material_id'],
                'color': 'Blue',
                'gender': 'male',
                'price': Decimal('29.99'),
                'article_number': f'TSH-IDS-{i:03d}',
                'sizes': [{'size': 'M', 'quantity': 10}]
            }
            product = product_service.create_product(product_data)
            assert product is not None, f"Failed to create product {i}"
            product_ids.append(product.id)
        
        # Get products by IDs
        products = product_service.get_products_by_ids(product_ids)
        assert len(products) == 3
        
        retrieved_ids = [p.id for p in products]
        for product_id in product_ids:
            assert product_id in retrieved_ids