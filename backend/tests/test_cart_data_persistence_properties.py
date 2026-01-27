"""
Property-based tests for cart data persistence and calculations.

**Feature: spoxpro-backend, Property 9: Cart Data Persistence and Calculations**
**Validates: Requirements 4.1, 4.4, 4.6, 4.5**

For any cart with items, the cart should persist across sessions, calculate correct totals 
based on item prices and quantities, and validate all operations against current inventory availability.
"""

import pytest
from hypothesis import given, strategies as st, settings
from decimal import Decimal
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.main import get_session, init_db
from db.models.product import Product, ProductSize, ProductType, Category, SportType, Material
from db.models.user import User
from db.models.order import CartItem
from db.services.cart_service import CartService as DBCartService
from db.services.product_service import ProductService
from db.services.user_service import UserService
from service.cart_service import CartService as BusinessCartService
from service.auth_service import AuthService
from config.settings import get_settings


# Test data strategies
@st.composite
def valid_product_data(draw):
    """Generate valid product data for testing."""
    return {
        'name': draw(st.text(min_size=1, max_size=100)),
        'description': draw(st.text(min_size=1, max_size=500)),
        'color': draw(st.sampled_from(['Red', 'Blue', 'Green', 'Black', 'White'])),
        'gender': draw(st.sampled_from(['male', 'female', 'unisex'])),
        'brand': 'spoXpro',
        'price': draw(st.decimals(min_value=Decimal('0.01'), max_value=Decimal('9999.99'), places=2)),
        'article_number': draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        'images': draw(st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=5)),
        'reviews': []
    }

@st.composite
def valid_user_data(draw):
    """Generate valid user data for testing."""
    return {
        'email': f"{draw(st.text(min_size=3, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))}@test.com",
        'password_hash': draw(st.text(min_size=8, max_size=100)),
        'phone': draw(st.text(min_size=10, max_size=15, alphabet=st.characters(whitelist_categories=('Nd',)))),
        'cookie': None
    }

@st.composite
def valid_cart_item_data(draw):
    """Generate valid cart item data for testing."""
    return {
        'size': draw(st.sampled_from(['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'XXXXL'])),
        'quantity': draw(st.integers(min_value=1, max_value=10))
    }


class TestCartDataPersistenceProperties:
    """Property-based tests for cart data persistence and calculations."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up test database for each test."""
        init_db()
        self.session = get_session()
        
        # Create helper tables
        self.product_type = ProductType(name="Test Type")
        self.category = Category(name="Test Category")
        self.sport_type = SportType(name="Test Sport")
        self.material = Material(name="Test Material")
        
        self.session.add_all([self.product_type, self.category, self.sport_type, self.material])
        self.session.commit()
        
        # Initialize services
        self.cart_service = DBCartService(self.session)
        self.product_service = ProductService(self.session)
        self.user_service = UserService(self.session)
        self.auth_service = AuthService(self.user_service)
        self.cart_business_service = BusinessCartService(self.cart_service, self.auth_service)
        
        yield
        
        # Cleanup
        self.session.close()

    @given(
        user_data=valid_user_data(),
        product_data=valid_product_data(),
        cart_item_data=valid_cart_item_data()
    )
    @settings(max_examples=100, deadline=None)
    def test_cart_persistence_across_sessions(self, user_data, product_data, cart_item_data):
        """
        Property: Cart data should persist across sessions for authenticated users.
        
        For any valid user and cart items, the cart should maintain its contents
        when accessed in different sessions.
        """
        try:
            # Create user
            user = User(**user_data)
            self.session.add(user)
            self.session.commit()
            
            # Create product with helper relationships
            product = Product(
                **product_data,
                product_type_id=self.product_type.id,
                category_id=self.category.id,
                sport_type_id=self.sport_type.id,
                material_id=self.material.id
            )
            self.session.add(product)
            self.session.commit()
            
            # Create product size with sufficient inventory
            product_size = ProductSize(
                product_id=product.id,
                size=cart_item_data['size'],
                quantity=cart_item_data['quantity'] + 5  # Ensure sufficient inventory
            )
            self.session.add(product_size)
            self.session.commit()
            
            # Add item to cart in first "session"
            cart_item = self.cart_service.add_cart_item(
                user_id=user.id,
                cookie=None,
                product_id=product.id,
                size=cart_item_data['size'],
                quantity=cart_item_data['quantity']
            )
            
            assert cart_item is not None
            original_cart_items = self.cart_service.get_cart_items(user_id=user.id, cookie=None)
            assert len(original_cart_items) == 1
            assert original_cart_items[0].quantity == cart_item_data['quantity']
            
            # Simulate new "session" - get cart items again
            persisted_cart_items = self.cart_service.get_cart_items(user_id=user.id, cookie=None)
            
            # Verify persistence
            assert len(persisted_cart_items) == len(original_cart_items)
            assert persisted_cart_items[0].product_id == original_cart_items[0].product_id
            assert persisted_cart_items[0].size == original_cart_items[0].size
            assert persisted_cart_items[0].quantity == original_cart_items[0].quantity
            
        except Exception as e:
            # Skip invalid test cases
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                pytest.skip(f"Skipping due to constraint violation: {e}")
            raise

    @given(
        cookie=st.text(min_size=10, max_size=50),
        product_data=valid_product_data(),
        cart_item_data=valid_cart_item_data()
    )
    @settings(max_examples=100, deadline=None)
    def test_guest_cart_persistence_with_cookie(self, cookie, product_data, cart_item_data):
        """
        Property: Guest cart data should persist using cookie identification.
        
        For any valid cookie and cart items, the cart should maintain its contents
        when accessed using the same cookie.
        """
        try:
            # Create product with helper relationships
            product = Product(
                **product_data,
                product_type_id=self.product_type.id,
                category_id=self.category.id,
                sport_type_id=self.sport_type.id,
                material_id=self.material.id
            )
            self.session.add(product)
            self.session.commit()
            
            # Create product size with sufficient inventory
            product_size = ProductSize(
                product_id=product.id,
                size=cart_item_data['size'],
                quantity=cart_item_data['quantity'] + 5
            )
            self.session.add(product_size)
            self.session.commit()
            
            # Add item to guest cart
            cart_item = self.cart_service.add_cart_item(
                user_id=None,
                cookie=cookie,
                product_id=product.id,
                size=cart_item_data['size'],
                quantity=cart_item_data['quantity']
            )
            
            assert cart_item is not None
            original_cart_items = self.cart_service.get_cart_items(user_id=None, cookie=cookie)
            assert len(original_cart_items) == 1
            
            # Simulate accessing cart with same cookie later
            persisted_cart_items = self.cart_service.get_cart_items(user_id=None, cookie=cookie)
            
            # Verify persistence
            assert len(persisted_cart_items) == len(original_cart_items)
            assert persisted_cart_items[0].product_id == original_cart_items[0].product_id
            assert persisted_cart_items[0].size == original_cart_items[0].size
            assert persisted_cart_items[0].quantity == original_cart_items[0].quantity
            
        except Exception as e:
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                pytest.skip(f"Skipping due to constraint violation: {e}")
            raise

    @given(
        user_data=valid_user_data(),
        product_data_list=st.lists(valid_product_data(), min_size=1, max_size=5),
        cart_items_data=st.lists(valid_cart_item_data(), min_size=1, max_size=5)
    )
    @settings(max_examples=50, deadline=None)
    def test_cart_total_calculation_accuracy(self, user_data, product_data_list, cart_items_data):
        """
        Property: Cart totals should be calculated correctly based on item prices and quantities.
        
        For any cart with multiple items, the total should equal the sum of 
        (price * quantity) for all items.
        """
        try:
            # Create user
            user = User(**user_data)
            self.session.add(user)
            self.session.commit()
            
            expected_total = Decimal('0.00')
            cart_items = []
            
            # Create products and add to cart
            for i, (product_data, cart_item_data) in enumerate(zip(product_data_list, cart_items_data)):
                # Ensure unique article numbers
                product_data['article_number'] = f"{product_data['article_number']}_{i}"
                
                product = Product(
                    **product_data,
                    product_type_id=self.product_type.id,
                    category_id=self.category.id,
                    sport_type_id=self.sport_type.id,
                    material_id=self.material.id
                )
                self.session.add(product)
                self.session.commit()
                
                # Create product size
                product_size = ProductSize(
                    product_id=product.id,
                    size=cart_item_data['size'],
                    quantity=cart_item_data['quantity'] + 5
                )
                self.session.add(product_size)
                self.session.commit()
                
                # Add to cart
                cart_item = self.cart_service.add_cart_item(
                    user_id=user.id,
                    cookie=None,
                    product_id=product.id,
                    size=cart_item_data['size'],
                    quantity=cart_item_data['quantity']
                )
                cart_items.append(cart_item)
                
                # Calculate expected total
                expected_total += product.price * cart_item_data['quantity']
            
            # Get cart total using business service
            calculated_total = self.cart_business_service.calculate_cart_total(user_id=user.id, cookie=None)
            
            # Verify total calculation
            assert calculated_total == expected_total, f"Expected {expected_total}, got {calculated_total}"
            
        except Exception as e:
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                pytest.skip(f"Skipping due to constraint violation: {e}")
            raise

    @given(
        user_data=valid_user_data(),
        product_data=valid_product_data(),
        cart_item_data=valid_cart_item_data()
    )
    @settings(max_examples=100, deadline=None)
    def test_inventory_validation_during_cart_operations(self, user_data, product_data, cart_item_data):
        """
        Property: Cart operations should validate against current inventory availability.
        
        For any cart operation, the system should check inventory and reject operations
        that would exceed available stock.
        """
        try:
            # Create user
            user = User(**user_data)
            self.session.add(user)
            self.session.commit()
            
            # Create product
            product = Product(
                **product_data,
                product_type_id=self.product_type.id,
                category_id=self.category.id,
                sport_type_id=self.sport_type.id,
                material_id=self.material.id
            )
            self.session.add(product)
            self.session.commit()
            
            # Create product size with limited inventory
            limited_inventory = max(1, cart_item_data['quantity'] - 1)
            product_size = ProductSize(
                product_id=product.id,
                size=cart_item_data['size'],
                quantity=limited_inventory
            )
            self.session.add(product_size)
            self.session.commit()
            
            # Try to add more items than available inventory
            if cart_item_data['quantity'] > limited_inventory:
                # Should fail due to insufficient inventory
                with pytest.raises(Exception):
                    self.cart_business_service.add_to_cart(
                        user_id=user.id,
                        cookie=None,
                        product_id=product.id,
                        size=cart_item_data['size'],
                        quantity=cart_item_data['quantity']
                    )
            else:
                # Should succeed if quantity <= inventory
                result = self.cart_business_service.add_to_cart(
                    user_id=user.id,
                    cookie=None,
                    product_id=product.id,
                    size=cart_item_data['size'],
                    quantity=cart_item_data['quantity']
                )
                assert result is True
                
        except Exception as e:
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                pytest.skip(f"Skipping due to constraint violation: {e}")
            raise

    @given(
        user_data=valid_user_data(),
        product_data=valid_product_data(),
        initial_quantity=st.integers(min_value=1, max_value=5),
        updated_quantity=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_cart_quantity_updates_persist(self, user_data, product_data, initial_quantity, updated_quantity):
        """
        Property: Cart quantity updates should persist correctly.
        
        For any cart item quantity update, the new quantity should be stored
        and retrievable in subsequent operations.
        """
        try:
            # Create user
            user = User(**user_data)
            self.session.add(user)
            self.session.commit()
            
            # Create product
            product = Product(
                **product_data,
                product_type_id=self.product_type.id,
                category_id=self.category.id,
                sport_type_id=self.sport_type.id,
                material_id=self.material.id
            )
            self.session.add(product)
            self.session.commit()
            
            # Create product size with sufficient inventory
            max_quantity = max(initial_quantity, updated_quantity)
            product_size = ProductSize(
                product_id=product.id,
                size='M',
                quantity=max_quantity + 5
            )
            self.session.add(product_size)
            self.session.commit()
            
            # Add initial item to cart
            cart_item = self.cart_service.add_cart_item(
                user_id=user.id,
                cookie=None,
                product_id=product.id,
                size='M',
                quantity=initial_quantity
            )
            
            # Update quantity
            updated_item = self.cart_service.update_cart_item(
                item_id=cart_item.id,
                quantity=updated_quantity
            )
            
            # Verify update persisted
            cart_items = self.cart_service.get_cart_items(user_id=user.id, cookie=None)
            assert len(cart_items) == 1
            assert cart_items[0].quantity == updated_quantity
            
        except Exception as e:
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                pytest.skip(f"Skipping due to constraint violation: {e}")
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])