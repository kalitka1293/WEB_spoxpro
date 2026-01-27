"""
Property-based tests for guest cookie management functionality.

**Feature: spoxpro-backend, Property 7: Guest Cookie Management**
**Validates: Requirements 3.1, 3.2**

For any first-time visitor without cookies, the system should generate a unique cookie,
and for any returning visitor with a valid cookie, the system should retrieve their
associated cart data.
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
from db.services.user_service import UserService
from db.services.cart_service import CartService as DBCartService
from db.services.product_service import ProductService
from db.main import get_db_session
from config.database import Base, engine


# Custom strategies for test data generation
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
def invalid_guest_cookie_strategy(draw):
    """Generate invalid guest cookie strings."""
    choice = draw(st.integers(0, 4))
    
    if choice == 0:
        # Wrong prefix
        suffix = ''.join(draw(st.lists(
            st.sampled_from(string.ascii_letters + string.digits),
            min_size=32,
            max_size=32
        )))
        return f"invalid_{suffix}"
    elif choice == 1:
        # Wrong length (too short)
        suffix = ''.join(draw(st.lists(
            st.sampled_from(string.ascii_letters + string.digits),
            min_size=1,
            max_size=20
        )))
        return f"guest_{suffix}"
    elif choice == 2:
        # Wrong length (too long)
        suffix = ''.join(draw(st.lists(
            st.sampled_from(string.ascii_letters + string.digits),
            min_size=40,
            max_size=60
        )))
        return f"guest_{suffix}"
    elif choice == 3:
        # Invalid characters
        return "guest_" + "!@#$%^&*()_+{}|:<>?[]\\;'\",./"[:32]
    else:
        # Empty or None-like
        return draw(st.sampled_from(["", "guest_", "guest"]))


class TestGuestCookieManagementProperties:
    """Property-based tests for guest cookie management."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a clean database for each test."""
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Get database session
        self.db = get_db_session()
        self.user_service = UserService(self.db)
        self.auth_service = AuthService(self.user_service)
        self.cart_service = DBCartService(self.db)
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
    
    # ==================== COOKIE GENERATION PROPERTIES ====================
    
    @given(st.data())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_first_time_visitor_gets_unique_cookie(self, data):
        """
        Property: For any first-time visitor without cookies, the system should 
        generate a unique cookie.
        
        **Validates: Requirements 3.1**
        """
        # Generate multiple cookies to test uniqueness
        num_cookies = data.draw(st.integers(min_value=2, max_value=10))
        generated_cookies = []
        
        for _ in range(num_cookies):
            # Generate guest cookie
            cookie_data = self.auth_service.generate_guest_cookie()
            
            # Property assertions
            assert cookie_data is not None, "Cookie generation should not fail"
            assert "cookie" in cookie_data, "Cookie data should contain 'cookie' field"
            assert "expires_at" in cookie_data, "Cookie data should contain 'expires_at' field"
            
            cookie = cookie_data["cookie"]
            expires_at = cookie_data["expires_at"]
            
            # Validate cookie format
            assert isinstance(cookie, str), "Cookie should be a string"
            assert cookie.startswith("guest_"), "Cookie should start with 'guest_'"
            assert len(cookie) == 38, "Cookie should be 38 characters long (guest_ + 32 chars)"
            
            # Validate cookie characters (alphanumeric after prefix)
            cookie_suffix = cookie[6:]  # Remove "guest_" prefix
            assert cookie_suffix.isalnum(), "Cookie suffix should be alphanumeric"
            
            # Validate expiration time
            assert isinstance(expires_at, datetime), "Expires_at should be a datetime"
            assert expires_at > datetime.utcnow(), "Cookie should not be expired"
            
            # Validate cookie using auth service
            assert self.auth_service.validate_guest_cookie(cookie), "Generated cookie should be valid"
            
            generated_cookies.append(cookie)
        
        # All cookies should be unique
        assert len(set(generated_cookies)) == len(generated_cookies), "All generated cookies should be unique"
    
    @given(
        invalid_cookie=invalid_guest_cookie_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_invalid_cookie_validation_fails(self, invalid_cookie):
        """
        Property: For any invalid cookie format, validation should fail.
        
        **Validates: Requirements 3.1**
        """
        # Invalid cookie validation should fail
        is_valid = self.auth_service.validate_guest_cookie(invalid_cookie)
        assert not is_valid, f"Invalid cookie should not validate: {invalid_cookie}"
    
    @given(
        valid_cookie=valid_guest_cookie_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_valid_cookie_validation_succeeds(self, valid_cookie):
        """
        Property: For any valid cookie format, validation should succeed.
        
        **Validates: Requirements 3.1**
        """
        # Valid cookie validation should succeed
        is_valid = self.auth_service.validate_guest_cookie(valid_cookie)
        assert is_valid, f"Valid cookie should validate: {valid_cookie}"
    
    # ==================== CART DATA ASSOCIATION PROPERTIES ====================
    
    @given(st.data())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_guest_cookie_cart_data_association(self, data):
        """
        Property: For any guest with a valid cookie, cart operations should 
        associate data with their cookie identifier.
        
        **Validates: Requirements 3.2**
        """
        # Create a simple test product
        product_data = {
            "name": "Test Product",
            "description": "Test Description",
            "product_type_id": 1,
            "category_id": 1,
            "sport_type_id": 1,
            "color": "Blue",
            "gender": "unisex",
            "brand": "spoXpro",
            "price": Decimal("29.99"),
            "reviews": [],
            "article_number": f"TEST{data.draw(st.integers(min_value=1000, max_value=9999))}",
            "images": ["test.jpg"],
            "material_id": 1,
            "sizes": [
                {"size": "M", "quantity": 50}
            ]
        }
        
        product = None
        cookie = None
        try:
            # Create a product for testing
            product = self.product_service.create_product(product_data)
            assume(product is not None)  # Skip if product creation fails
            
            # Generate guest cookie
            cookie_data = self.auth_service.generate_guest_cookie()
            cookie = cookie_data["cookie"]
            
            # Add item to cart using cookie
            cart_item = self.cart_service.add_cart_item(
                user_id=None,
                cookie=cookie,
                product_id=product.id,
                size="M",
                quantity=2
            )
            
            # Property assertions
            assert cart_item is not None, "Cart item should be created for guest"
            assert cart_item.cookie == cookie, "Cart item should be associated with guest cookie"
            assert cart_item.user_id is None, "Cart item should not have user_id for guest"
            assert cart_item.product_id == product.id, "Cart item should reference correct product"
            assert cart_item.size == "M", "Cart item should have correct size"
            assert cart_item.quantity == 2, "Cart item should have correct quantity"
            
            # Retrieve cart items using cookie
            cart_items = self.cart_service.get_cart_items(user_id=None, cookie=cookie)
            
            # Property assertions for retrieval
            assert len(cart_items) == 1, "Should retrieve exactly one cart item"
            retrieved_item = cart_items[0]
            assert retrieved_item.id == cart_item.id, "Retrieved item should match created item"
            assert retrieved_item.cookie == cookie, "Retrieved item should have correct cookie"
            
        finally:
            # Clean up - clear cart first, then delete product
            if cookie:
                try:
                    self.cart_service.clear_cart(user_id=None, cookie=cookie)
                except:
                    pass
            if product:
                try:
                    self.product_service.delete_product(product.id)
                except:
                    pass
    
    @given(st.data())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_returning_visitor_cart_persistence(self, data):
        """
        Property: For any returning visitor with a valid cookie, the system should 
        retrieve their associated cart data and maintain persistence across sessions.
        
        **Validates: Requirements 3.2**
        """
        # Create a simple test product
        product_data = {
            "name": "Test Product 2",
            "description": "Test Description 2",
            "product_type_id": 1,
            "category_id": 1,
            "sport_type_id": 1,
            "color": "Red",
            "gender": "unisex",
            "brand": "spoXpro",
            "price": Decimal("39.99"),
            "reviews": [],
            "article_number": f"TEST2{data.draw(st.integers(min_value=1000, max_value=9999))}",
            "images": ["test2.jpg"],
            "material_id": 1,
            "sizes": [
                {"size": "L", "quantity": 50}
            ]
        }
        
        product = None
        cookie = None
        try:
            # Create a product for testing
            product = self.product_service.create_product(product_data)
            assume(product is not None)  # Skip if product creation fails
            
            # Generate guest cookie
            cookie_data = self.auth_service.generate_guest_cookie()
            cookie = cookie_data["cookie"]
            
            # First session: Add item to cart
            cart_item1 = self.cart_service.add_cart_item(
                user_id=None,
                cookie=cookie,
                product_id=product.id,
                size="L",
                quantity=1
            )
            assert cart_item1 is not None, "First cart item should be created"
            
            # Simulate returning visitor: Retrieve cart data
            cart_items_session1 = self.cart_service.get_cart_items(user_id=None, cookie=cookie)
            assert len(cart_items_session1) == 1, "Should retrieve cart from first session"
            assert cart_items_session1[0].quantity == 1, "Should have correct quantity from first session"
            
            # Second session: Add more of the same item (should update quantity)
            cart_item2 = self.cart_service.add_cart_item(
                user_id=None,
                cookie=cookie,
                product_id=product.id,
                size="L",
                quantity=2
            )
            assert cart_item2 is not None, "Second cart addition should succeed"
            
            # Verify cart persistence and quantity update
            cart_items_session2 = self.cart_service.get_cart_items(user_id=None, cookie=cookie)
            assert len(cart_items_session2) == 1, "Should still have one cart item (same product/size)"
            
            expected_total_quantity = 3  # 1 + 2
            assert cart_items_session2[0].quantity == expected_total_quantity, \
                f"Quantity should be updated to {expected_total_quantity}"
            
            # Verify cart total calculation
            cart_total = self.cart_service.calculate_cart_total(user_id=None, cookie=cookie)
            expected_total = product.price * Decimal(str(expected_total_quantity))
            assert cart_total == expected_total, "Cart total should be calculated correctly"
            
        finally:
            # Clean up - clear cart first, then delete product
            if cookie:
                try:
                    self.cart_service.clear_cart(user_id=None, cookie=cookie)
                except:
                    pass
            if product:
                try:
                    self.product_service.delete_product(product.id)
                except:
                    pass
    
    # ==================== COOKIE ISOLATION PROPERTIES ====================
    
    @given(st.data())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_different_cookies_isolated_carts(self, data):
        """
        Property: For any two different guest cookies, their cart data should be 
        completely isolated from each other.
        
        **Validates: Requirements 3.2**
        """
        # Create a simple test product
        product_data = {
            "name": "Test Product 3",
            "description": "Test Description 3",
            "product_type_id": 1,
            "category_id": 1,
            "sport_type_id": 1,
            "color": "Green",
            "gender": "unisex",
            "brand": "spoXpro",
            "price": Decimal("49.99"),
            "reviews": [],
            "article_number": f"TEST3{data.draw(st.integers(min_value=1000, max_value=9999))}",
            "images": ["test3.jpg"],
            "material_id": 1,
            "sizes": [
                {"size": "S", "quantity": 50}
            ]
        }
        
        product = None
        cookie1 = None
        cookie2 = None
        try:
            # Create a product for testing
            product = self.product_service.create_product(product_data)
            assume(product is not None)  # Skip if product creation fails
            
            # Generate two different guest cookies
            cookie_data1 = self.auth_service.generate_guest_cookie()
            cookie_data2 = self.auth_service.generate_guest_cookie()
            cookie1 = cookie_data1["cookie"]
            cookie2 = cookie_data2["cookie"]
            
            # Ensure cookies are different
            assume(cookie1 != cookie2)
            
            # Add items to first guest's cart
            cart_item1 = self.cart_service.add_cart_item(
                user_id=None,
                cookie=cookie1,
                product_id=product.id,
                size="S",
                quantity=2
            )
            assert cart_item1 is not None, "First guest cart item should be created"
            
            # Add items to second guest's cart
            cart_item2 = self.cart_service.add_cart_item(
                user_id=None,
                cookie=cookie2,
                product_id=product.id,
                size="S",
                quantity=3
            )
            assert cart_item2 is not None, "Second guest cart item should be created"
            
            # Verify cart isolation
            cart_items1 = self.cart_service.get_cart_items(user_id=None, cookie=cookie1)
            cart_items2 = self.cart_service.get_cart_items(user_id=None, cookie=cookie2)
            
            # Property assertions for isolation
            assert len(cart_items1) == 1, "First guest should have exactly one cart item"
            assert len(cart_items2) == 1, "Second guest should have exactly one cart item"
            
            assert cart_items1[0].cookie == cookie1, "First cart item should belong to first cookie"
            assert cart_items2[0].cookie == cookie2, "Second cart item should belong to second cookie"
            
            assert cart_items1[0].quantity == 2, "First guest should have correct quantity"
            assert cart_items2[0].quantity == 3, "Second guest should have correct quantity"
            
            # Verify cart totals are independent
            total1 = self.cart_service.calculate_cart_total(user_id=None, cookie=cookie1)
            total2 = self.cart_service.calculate_cart_total(user_id=None, cookie=cookie2)
            
            expected_total1 = product.price * Decimal("2")
            expected_total2 = product.price * Decimal("3")
            
            assert total1 == expected_total1, "First guest cart total should be correct"
            assert total2 == expected_total2, "Second guest cart total should be correct"
            
        finally:
            # Clean up - clear carts first, then delete product
            if cookie1:
                try:
                    self.cart_service.clear_cart(user_id=None, cookie=cookie1)
                except:
                    pass
            if cookie2:
                try:
                    self.cart_service.clear_cart(user_id=None, cookie=cookie2)
                except:
                    pass
            if product:
                try:
                    self.product_service.delete_product(product.id)
                except:
                    pass
    
    # ==================== EDGE CASE PROPERTIES ====================
    
    @given(st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_empty_cookie_handling(self, data):
        """
        Property: For any empty or None cookie values, cart operations should 
        handle them gracefully without crashing.
        
        **Validates: Requirements 3.1, 3.2**
        """
        # Test various empty/invalid cookie values
        invalid_cookies = [None, "", "   ", "invalid"]
        
        for invalid_cookie in invalid_cookies:
            # Cart operations should handle invalid cookies gracefully
            cart_items = self.cart_service.get_cart_items(user_id=None, cookie=invalid_cookie)
            assert isinstance(cart_items, list), "get_cart_items should return a list even for invalid cookies"
            
            cart_total = self.cart_service.calculate_cart_total(user_id=None, cookie=invalid_cookie)
            assert cart_total == Decimal('0.00'), "Cart total should be zero for invalid cookies"
            
            # Validation should fail for invalid cookies
            if invalid_cookie:  # Skip None values for validation
                is_valid = self.auth_service.validate_guest_cookie(invalid_cookie)
                assert not is_valid, f"Invalid cookie should not validate: {invalid_cookie}"
    
    @given(
        num_operations=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_concurrent_cookie_generation_uniqueness(self, num_operations):
        """
        Property: For any number of concurrent cookie generations, all cookies 
        should be unique and valid.
        
        **Validates: Requirements 3.1**
        """
        # Generate multiple cookies rapidly to test uniqueness
        cookies = []
        
        for _ in range(num_operations):
            cookie_data = self.auth_service.generate_guest_cookie()
            assert cookie_data is not None, "Cookie generation should not fail"
            
            cookie = cookie_data["cookie"]
            assert self.auth_service.validate_guest_cookie(cookie), "Generated cookie should be valid"
            
            cookies.append(cookie)
        
        # All cookies should be unique
        unique_cookies = set(cookies)
        assert len(unique_cookies) == len(cookies), \
            f"All {num_operations} cookies should be unique, but got {len(unique_cookies)} unique out of {len(cookies)}"
        
        # All cookies should have proper format
        for cookie in cookies:
            assert cookie.startswith("guest_"), "All cookies should start with 'guest_'"
            assert len(cookie) == 38, "All cookies should be 38 characters long"
            assert cookie[6:].isalnum(), "All cookie suffixes should be alphanumeric"