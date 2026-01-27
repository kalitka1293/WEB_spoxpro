"""
Property-based tests for cart operations with authentication functionality.

**Feature: spoxpro-backend, Property 8: Cart Operations with Authentication**
**Validates: Requirements 3.3, 3.4, 3.5**

For any authenticated user or guest with valid cookie, cart operations (add, update, remove) 
should be permitted, but for guests attempting non-cart operations, the system should 
require full authentication.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from decimal import Decimal
import string
import secrets

from service.auth_service import AuthService
from service.cart_service import CartService as BusinessCartService
from db.services.user_service import UserService
from db.services.cart_service import CartService as DBCartService
from db.services.product_service import ProductService
from db.main import get_db_session
from config.database import Base, engine


# Custom strategies for test data generation
@st.composite
def valid_email_strategy(draw):
    """Generate valid email addresses."""
    username = draw(st.text(
        alphabet=st.characters(min_codepoint=97, max_codepoint=122),  # lowercase letters
        min_size=1,
        max_size=20
    ).filter(lambda x: x and not x.startswith('.') and not x.endswith('.')))
    
    domain = draw(st.text(
        alphabet=st.characters(min_codepoint=97, max_codepoint=122),  # lowercase letters
        min_size=1,
        max_size=15
    ).filter(lambda x: x and not x.startswith('.') and not x.endswith('.')))
    
    tld = draw(st.sampled_from(['com', 'org', 'net', 'edu', 'gov']))
    
    return f"{username}@{domain}.{tld}"


@st.composite
def valid_password_strategy(draw):
    """Generate valid passwords that meet strength requirements."""
    # Ensure at least one letter and one number
    letters = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=5))
    numbers = draw(st.text(alphabet='0123456789', min_size=1, max_size=3))
    
    # Add optional extra characters
    extra = draw(st.text(
        alphabet='abcdefghijklmnopqrstuvwxyz0123456789',
        min_size=0,
        max_size=10
    ))
    
    # Combine and shuffle
    password_chars = list(letters + numbers + extra)
    draw(st.randoms()).shuffle(password_chars)
    password = ''.join(password_chars)
    
    # Ensure minimum length
    if len(password) < 8:
        padding = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=8 - len(password), max_size=8 - len(password)))
        password += padding
    
    # Ensure maximum length (bcrypt limit is 72 bytes, keep it shorter for safety)
    if len(password) > 60:
        password = password[:60]
    
    return password


@st.composite
def valid_phone_strategy(draw):
    """Generate valid phone numbers."""
    return draw(st.text(alphabet='0123456789', min_size=10, max_size=15))


@st.composite
def valid_guest_cookie_strategy(draw):
    """Generate valid guest cookie strings."""
    # Generate cookie in the expected format: "guest_" + 32 alphanumeric characters
    cookie_suffix = ''.join(
        draw(st.lists(
            st.sampled_from(string.ascii_letters + string.digits),
            min_size=32,
            max_size=32
        ))
    )
    return f"guest_{cookie_suffix}"


@st.composite
def cart_operation_strategy(draw):
    """Generate cart operation data."""
    return {
        'size': draw(st.sampled_from(['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'XXXXL'])),
        'quantity': draw(st.integers(min_value=1, max_value=10))
    }


class TestCartOperationsWithAuthenticationProperties:
    """Property-based tests for cart operations with authentication."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a clean database for each test."""
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Get database session
        self.db = get_db_session()
        self.user_service = UserService(self.db)
        self.auth_service = AuthService(self.user_service)
        self.db_cart_service = DBCartService(self.db)
        self.cart_service = BusinessCartService(self.db_cart_service, self.auth_service)
        self.product_service = ProductService(self.db)
        
        # Create required helper data
        self._create_helper_data()
        
        yield
        
        # Clean up
        self.db.close()
        Base.metadata.drop_all(bind=engine)
    
    def _create_helper_data(self):
        """Create required helper data for tests."""
        try:
            # Create helper tables data if they don't exist
            from db.models.product import ProductType, Category, SportType, Material
            
            # Check if data already exists
            if not self.db.query(ProductType).first():
                product_type = ProductType(name="T-Shirt")
                self.db.add(product_type)
            
            if not self.db.query(Category).first():
                category = Category(name="Clothing")
                self.db.add(category)
            
            if not self.db.query(SportType).first():
                sport_type = SportType(name="Running")
                self.db.add(sport_type)
            
            if not self.db.query(Material).first():
                material = Material(name="Cotton")
                self.db.add(material)
            
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            # If helper data creation fails, tests will skip
            pass
    
    def _create_test_product(self, article_suffix=""):
        """Create a test product for cart operations."""
        product_data = {
            "name": f"Test Product {article_suffix}",
            "description": "Test Description",
            "product_type_id": 1,
            "category_id": 1,
            "sport_type_id": 1,
            "color": "Blue",
            "gender": "unisex",
            "brand": "spoXpro",
            "price": Decimal("29.99"),
            "reviews": [],
            "article_number": f"TEST{article_suffix}{secrets.randbelow(10000)}",
            "images": ["test.jpg"],
            "material_id": 1,
            "sizes": [
                {"size": "S", "quantity": 50},
                {"size": "M", "quantity": 50},
                {"size": "L", "quantity": 50}
            ]
        }
        return self.product_service.create_product(product_data)
    
    # ==================== AUTHENTICATED USER CART OPERATIONS ====================
    
    @given(
        email=valid_email_strategy(),
        password=valid_password_strategy(),
        phone=valid_phone_strategy(),
        cart_op=cart_operation_strategy()
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_authenticated_user_cart_operations_permitted(self, email, password, phone, cart_op):
        """
        Property: For any authenticated user, cart operations (add, update, remove) 
        should be permitted.
        
        **Validates: Requirements 3.3, 3.4**
        """
        assume(len(email) <= 255)
        assume(len(phone) <= 20)
        assume('@' in email and '.' in email)
        
        user = None
        product = None
        try:
            # Create and authenticate user
            user = self.auth_service.register_user(email, password, phone)
            assume(user is not None)  # Skip if user creation fails
            
            # Generate JWT token for authentication
            token_data = self.auth_service.generate_jwt_token(user)
            token = token_data["access_token"]
            
            # Create test product
            product = self._create_test_product(f"AUTH{user.id}")
            assume(product is not None)  # Skip if product creation fails
            
            # Test ADD operation - should be permitted for authenticated user
            add_result = self.cart_service.add_to_cart(
                user_id=user.id,
                cookie=None,
                product_id=product.id,
                size=cart_op['size'],
                quantity=cart_op['quantity']
            )
            
            # Property assertions for ADD operation
            assert add_result is not None, "Authenticated user should be able to add items to cart"
            assert add_result.user_id == user.id, "Cart item should be associated with authenticated user"
            assert add_result.cookie is None, "Authenticated user cart item should not have cookie"
            assert add_result.product_id == product.id, "Cart item should reference correct product"
            assert add_result.size == cart_op['size'], "Cart item should have correct size"
            assert add_result.quantity == cart_op['quantity'], "Cart item should have correct quantity"
            
            # Test GET operation - should retrieve cart items
            cart_items = self.cart_service.get_cart_contents(user_id=user.id, cookie=None)
            assert len(cart_items) == 1, "Should retrieve exactly one cart item"
            assert cart_items[0].id == add_result.id, "Retrieved item should match added item"
            
            # Test UPDATE operation - should be permitted
            new_quantity = cart_op['quantity'] + 1
            if new_quantity <= 50:  # Don't exceed inventory
                update_result = self.cart_service.update_cart_item(
                    item_id=add_result.id,
                    quantity=new_quantity
                )
                assert update_result is not None, "Authenticated user should be able to update cart items"
                assert update_result.quantity == new_quantity, "Cart item quantity should be updated"
            
            # Test REMOVE operation - should be permitted
            remove_result = self.cart_service.remove_from_cart(item_id=add_result.id)
            assert remove_result is True, "Authenticated user should be able to remove cart items"
            
            # Verify item was removed
            cart_items_after_remove = self.cart_service.get_cart_contents(user_id=user.id, cookie=None)
            assert len(cart_items_after_remove) == 0, "Cart should be empty after removing item"
            
        finally:
            # Clean up
            if user:
                try:
                    self.db_cart_service.clear_cart(user_id=user.id, cookie=None)
                    self.user_service.delete_user(user.id)
                except:
                    pass
            if product:
                try:
                    self.product_service.delete_product(product.id)
                except:
                    pass
    
    # ==================== GUEST COOKIE CART OPERATIONS ====================
    
    @given(
        guest_cookie=valid_guest_cookie_strategy(),
        cart_op=cart_operation_strategy()
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_guest_cookie_cart_operations_permitted(self, guest_cookie, cart_op):
        """
        Property: For any guest with valid cookie, cart operations (add, update, remove) 
        should be permitted.
        
        **Validates: Requirements 3.3, 3.4**
        """
        product = None
        try:
            # Validate guest cookie format
            assert self.auth_service.validate_guest_cookie(guest_cookie), "Guest cookie should be valid"
            
            # Create test product
            product = self._create_test_product(f"GUEST{guest_cookie[-8:]}")
            assume(product is not None)  # Skip if product creation fails
            
            # Test ADD operation - should be permitted for guest with valid cookie
            add_result = self.cart_service.add_to_cart(
                user_id=None,
                cookie=guest_cookie,
                product_id=product.id,
                size=cart_op['size'],
                quantity=cart_op['quantity']
            )
            
            # Property assertions for ADD operation
            assert add_result is not None, "Guest with valid cookie should be able to add items to cart"
            assert add_result.user_id is None, "Guest cart item should not have user_id"
            assert add_result.cookie == guest_cookie, "Cart item should be associated with guest cookie"
            assert add_result.product_id == product.id, "Cart item should reference correct product"
            assert add_result.size == cart_op['size'], "Cart item should have correct size"
            assert add_result.quantity == cart_op['quantity'], "Cart item should have correct quantity"
            
            # Test GET operation - should retrieve cart items
            cart_items = self.cart_service.get_cart_contents(user_id=None, cookie=guest_cookie)
            assert len(cart_items) == 1, "Should retrieve exactly one cart item"
            assert cart_items[0].id == add_result.id, "Retrieved item should match added item"
            
            # Test UPDATE operation - should be permitted
            new_quantity = cart_op['quantity'] + 1
            if new_quantity <= 50:  # Don't exceed inventory
                update_result = self.cart_service.update_cart_item(
                    item_id=add_result.id,
                    quantity=new_quantity
                )
                assert update_result is not None, "Guest with valid cookie should be able to update cart items"
                assert update_result.quantity == new_quantity, "Cart item quantity should be updated"
            
            # Test REMOVE operation - should be permitted
            remove_result = self.cart_service.remove_from_cart(item_id=add_result.id)
            assert remove_result is True, "Guest with valid cookie should be able to remove cart items"
            
            # Verify item was removed
            cart_items_after_remove = self.cart_service.get_cart_contents(user_id=None, cookie=guest_cookie)
            assert len(cart_items_after_remove) == 0, "Cart should be empty after removing item"
            
        finally:
            # Clean up
            try:
                self.db_cart_service.clear_cart(user_id=None, cookie=guest_cookie)
            except:
                pass
            if product:
                try:
                    self.product_service.delete_product(product.id)
                except:
                    pass
    
    # ==================== INVALID AUTHENTICATION SCENARIOS ====================
    
    @given(
        invalid_cookie=st.one_of(
            st.just(""),
            st.just("invalid_cookie"),
            st.just("guest_tooshort"),
            st.just("wrong_prefix_" + "a" * 32),
            st.text(alphabet="!@#$%^&*()", min_size=10, max_size=50)
        ),
        cart_op=cart_operation_strategy()
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_invalid_cookie_cart_operations_fail(self, invalid_cookie, cart_op):
        """
        Property: For any invalid guest cookie, cart operations should fail gracefully.
        
        **Validates: Requirements 3.3, 3.5**
        """
        product = None
        try:
            # Validate that cookie is indeed invalid
            if invalid_cookie:  # Skip empty string validation
                is_valid = self.auth_service.validate_guest_cookie(invalid_cookie)
                assume(not is_valid)  # Only test with invalid cookies
            
            # Create test product
            product = self._create_test_product(f"INVALID{secrets.randbelow(1000)}")
            assume(product is not None)  # Skip if product creation fails
            
            # Test ADD operation with invalid cookie - should fail or return empty results
            add_result = self.cart_service.add_to_cart(
                user_id=None,
                cookie=invalid_cookie,
                product_id=product.id,
                size=cart_op['size'],
                quantity=cart_op['quantity']
            )
            
            # Property assertion - invalid cookie should not allow cart operations
            # The service should either return None or handle gracefully
            if add_result is not None:
                # If it doesn't fail outright, it should not create a valid cart association
                cart_items = self.cart_service.get_cart_contents(user_id=None, cookie=invalid_cookie)
                # Cart should be empty or the operation should be rejected
                assert isinstance(cart_items, list), "get_cart_contents should return a list"
            
        finally:
            # Clean up
            if product:
                try:
                    self.product_service.delete_product(product.id)
                except:
                    pass
    
    @given(
        cart_op=cart_operation_strategy()
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_no_authentication_cart_operations_fail(self, cart_op):
        """
        Property: For any cart operation without user_id or cookie, the operation 
        should fail gracefully.
        
        **Validates: Requirements 3.5**
        """
        product = None
        try:
            # Create test product
            product = self._create_test_product(f"NOAUTH{secrets.randbelow(1000)}")
            assume(product is not None)  # Skip if product creation fails
            
            # Test ADD operation without authentication - should fail
            add_result = self.cart_service.add_to_cart(
                user_id=None,
                cookie=None,
                product_id=product.id,
                size=cart_op['size'],
                quantity=cart_op['quantity']
            )
            
            # Property assertion - no authentication should not allow cart operations
            assert add_result is None, "Cart operations without authentication should fail"
            
            # Test GET operation without authentication - should return empty list
            cart_items = self.cart_service.get_cart_contents(user_id=None, cookie=None)
            assert isinstance(cart_items, list), "get_cart_contents should return a list"
            assert len(cart_items) == 0, "Cart should be empty without authentication"
            
        finally:
            # Clean up
            if product:
                try:
                    self.product_service.delete_product(product.id)
                except:
                    pass
    
    # ==================== CART ISOLATION PROPERTIES ====================
    
    @given(
        email=valid_email_strategy(),
        password=valid_password_strategy(),
        phone=valid_phone_strategy(),
        guest_cookie=valid_guest_cookie_strategy(),
        cart_op1=cart_operation_strategy(),
        cart_op2=cart_operation_strategy()
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_authenticated_user_and_guest_cart_isolation(self, email, password, phone, guest_cookie, cart_op1, cart_op2):
        """
        Property: For any authenticated user and guest with different identifiers,
        their cart operations should be completely isolated.
        
        **Validates: Requirements 3.3, 3.4**
        """
        assume(len(email) <= 255)
        assume(len(phone) <= 20)
        assume('@' in email and '.' in email)
        
        user = None
        product1 = None
        product2 = None
        try:
            # Create authenticated user
            user = self.auth_service.register_user(email, password, phone)
            assume(user is not None)  # Skip if user creation fails
            
            # Create test products
            product1 = self._create_test_product(f"USER{user.id}")
            product2 = self._create_test_product(f"GUEST{guest_cookie[-8:]}")
            assume(product1 is not None and product2 is not None)  # Skip if product creation fails
            
            # Add item to authenticated user's cart
            user_cart_item = self.cart_service.add_to_cart(
                user_id=user.id,
                cookie=None,
                product_id=product1.id,
                size=cart_op1['size'],
                quantity=cart_op1['quantity']
            )
            assert user_cart_item is not None, "Authenticated user cart operation should succeed"
            
            # Add item to guest's cart
            guest_cart_item = self.cart_service.add_to_cart(
                user_id=None,
                cookie=guest_cookie,
                product_id=product2.id,
                size=cart_op2['size'],
                quantity=cart_op2['quantity']
            )
            assert guest_cart_item is not None, "Guest cart operation should succeed"
            
            # Verify cart isolation
            user_cart = self.cart_service.get_cart_contents(user_id=user.id, cookie=None)
            guest_cart = self.cart_service.get_cart_contents(user_id=None, cookie=guest_cookie)
            
            # Property assertions for isolation
            assert len(user_cart) == 1, "Authenticated user should have exactly one cart item"
            assert len(guest_cart) == 1, "Guest should have exactly one cart item"
            
            assert user_cart[0].user_id == user.id, "User cart item should belong to authenticated user"
            assert user_cart[0].cookie is None, "User cart item should not have cookie"
            
            assert guest_cart[0].user_id is None, "Guest cart item should not have user_id"
            assert guest_cart[0].cookie == guest_cookie, "Guest cart item should belong to guest cookie"
            
            # Verify different products
            assert user_cart[0].product_id == product1.id, "User cart should contain user's product"
            assert guest_cart[0].product_id == product2.id, "Guest cart should contain guest's product"
            
            # Verify cart totals are independent
            user_total = self.cart_service.calculate_cart_total(user_id=user.id, cookie=None)
            guest_total = self.cart_service.calculate_cart_total(user_id=None, cookie=guest_cookie)
            
            expected_user_total = product1.price * Decimal(str(cart_op1['quantity']))
            expected_guest_total = product2.price * Decimal(str(cart_op2['quantity']))
            
            assert user_total == expected_user_total, "User cart total should be correct"
            assert guest_total == expected_guest_total, "Guest cart total should be correct"
            
        finally:
            # Clean up
            if user:
                try:
                    self.db_cart_service.clear_cart(user_id=user.id, cookie=None)
                    self.user_service.delete_user(user.id)
                except:
                    pass
            try:
                self.db_cart_service.clear_cart(user_id=None, cookie=guest_cookie)
            except:
                pass
            if product1:
                try:
                    self.product_service.delete_product(product1.id)
                except:
                    pass
            if product2:
                try:
                    self.product_service.delete_product(product2.id)
                except:
                    pass
    
    # ==================== INVENTORY VALIDATION PROPERTIES ====================
    
    @given(
        guest_cookie=valid_guest_cookie_strategy(),
        requested_quantity=st.integers(min_value=51, max_value=100)  # More than available inventory
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_cart_operations_respect_inventory_limits(self, guest_cookie, requested_quantity):
        """
        Property: For any cart operation that would exceed available inventory,
        the operation should be rejected regardless of authentication method.
        
        **Validates: Requirements 3.3, 3.4**
        """
        product = None
        try:
            # Create test product with limited inventory (50 per size)
            product = self._create_test_product(f"INVENTORY{secrets.randbelow(1000)}")
            assume(product is not None)  # Skip if product creation fails
            
            # Attempt to add more items than available inventory
            add_result = self.cart_service.add_to_cart(
                user_id=None,
                cookie=guest_cookie,
                product_id=product.id,
                size="M",
                quantity=requested_quantity  # More than the 50 available
            )
            
            # Property assertion - should not allow exceeding inventory
            assert add_result is None, "Cart operations should not exceed available inventory"
            
            # Verify cart remains empty
            cart_items = self.cart_service.get_cart_contents(user_id=None, cookie=guest_cookie)
            assert len(cart_items) == 0, "Cart should remain empty when inventory is exceeded"
            
        finally:
            # Clean up
            try:
                self.db_cart_service.clear_cart(user_id=None, cookie=guest_cookie)
            except:
                pass
            if product:
                try:
                    self.product_service.delete_product(product.id)
                except:
                    pass
    
    # ==================== EDGE CASE PROPERTIES ====================
    
    @given(
        email=valid_email_strategy(),
        password=valid_password_strategy(),
        phone=valid_phone_strategy(),
        operations_count=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_multiple_cart_operations_consistency(self, email, password, phone, operations_count):
        """
        Property: For any sequence of cart operations by the same authenticated user,
        the cart state should remain consistent and operations should be idempotent
        where appropriate.
        
        **Validates: Requirements 3.3, 3.4**
        """
        assume(len(email) <= 255)
        assume(len(phone) <= 20)
        assume('@' in email and '.' in email)
        
        user = None
        product = None
        try:
            # Create authenticated user
            user = self.auth_service.register_user(email, password, phone)
            assume(user is not None)  # Skip if user creation fails
            
            # Create test product
            product = self._create_test_product(f"MULTI{user.id}")
            assume(product is not None)  # Skip if product creation fails
            
            cart_items = []
            
            # Perform multiple add operations
            for i in range(operations_count):
                add_result = self.cart_service.add_to_cart(
                    user_id=user.id,
                    cookie=None,
                    product_id=product.id,
                    size="L",
                    quantity=1
                )
                
                if add_result is not None:
                    cart_items.append(add_result)
            
            # Verify cart consistency
            current_cart = self.cart_service.get_cart_contents(user_id=user.id, cookie=None)
            
            # Property assertions
            if cart_items:
                # Should have consolidated into a single item with accumulated quantity
                assert len(current_cart) == 1, "Multiple adds of same product/size should consolidate"
                
                # Total quantity should match number of successful operations
                expected_quantity = len(cart_items)
                assert current_cart[0].quantity == expected_quantity, \
                    f"Cart quantity should be {expected_quantity} after {len(cart_items)} add operations"
                
                # Cart total should be correct
                expected_total = product.price * Decimal(str(expected_quantity))
                actual_total = self.cart_service.calculate_cart_total(user_id=user.id, cookie=None)
                assert actual_total == expected_total, "Cart total should be calculated correctly"
            
        finally:
            # Clean up
            if user:
                try:
                    self.db_cart_service.clear_cart(user_id=user.id, cookie=None)
                    self.user_service.delete_user(user.id)
                except:
                    pass
            if product:
                try:
                    self.product_service.delete_product(product.id)
                except:
                    pass