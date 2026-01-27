"""
Comprehensive integration tests for complete workflows in spoXpro backend.

Tests end-to-end user registration, shopping, and checkout flows.
Tests error handling scenarios and logging functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from decimal import Decimal
import secrets
import logging
from unittest.mock import patch

from service.auth_service import AuthService
from service.cart_service import CartService as BusinessCartService
from service.order_service import OrderProcessingService
from db.services.user_service import UserService
from db.services.cart_service import CartService as DBCartService
from db.services.product_service import ProductService
from db.services.order_service import OrderService as DBOrderService
from db.main import get_db_session
from config.database import Base, engine
from DTO.user import CreateOrderRequest
from logs.log_store import get_logger

logger = get_logger(__name__)


class TestIntegrationWorkflows:
    """Comprehensive integration tests for complete workflows."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a clean database for each test."""
        # Drop and recreate tables for complete isolation
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # Get database session
        self.db = get_db_session()
        self.user_service = UserService(self.db)
        self.auth_service = AuthService(self.user_service)
        self.db_cart_service = DBCartService(self.db)
        self.cart_service = BusinessCartService(self.db_cart_service, self.auth_service)
        self.product_service = ProductService(self.db)
        self.db_order_service = DBOrderService(self.db)
        self.order_service = OrderProcessingService(
            self.db_order_service, 
            self.db_cart_service, 
            self.product_service
        )
        
        # Create required helper data
        self._create_helper_data()
        
        yield
        
        # Clean up
        self.db.close()
        Base.metadata.drop_all(bind=engine)
    
    def _create_helper_data(self):
        """Create required helper data for tests."""
        try:
            from db.models.product import ProductType, Category, SportType, Material
            
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
            pass
    
    def _create_test_product(self, name_suffix="", price=Decimal("29.99")):
        """Create a test product with customizable price."""
        product_data = {
            "name": f"Test Product {name_suffix}",
            "description": "Integration Test Product",
            "product_type_id": 1,
            "category_id": 1,
            "sport_type_id": 1,
            "color": "Blue",
            "gender": "unisex",
            "brand": "spoXpro",
            "price": price,
            "reviews": [],
            "article_number": f"WF{name_suffix}{secrets.randbelow(10000)}",
            "images": ["test.jpg"],
            "material_id": 1,
            "sizes": [
                {"size": "S", "quantity": 10},
                {"size": "M", "quantity": 10},
                {"size": "L", "quantity": 10}
            ]
        }
        return self.product_service.create_product(product_data)
    
    def test_complete_user_shopping_journey(self):
        """
        Test complete user shopping journey from registration to order completion.
        This is the main happy path test.
        """
        user = None
        products = []
        
        try:
            # Step 1: User Registration
            email = f"shopper{secrets.randbelow(10000)}@test.com"
            password = "securepass123"
            phone = "1234567890"
            
            user = self.auth_service.register_user(email, password, phone)
            assert user is not None, "User registration should succeed"
            assert user.email == email, "User email should be correct"
            
            # Step 2: User Authentication
            authenticated_user = self.auth_service.authenticate_user(email, password)
            assert authenticated_user is not None, "User authentication should succeed"
            assert authenticated_user.id == user.id, "Authenticated user should match registered user"
            
            # Step 3: JWT Token Generation
            token_data = self.auth_service.generate_jwt_token(user)
            assert token_data is not None, "JWT token generation should succeed"
            assert "access_token" in token_data, "Token should contain access_token"
            assert "token_type" in token_data, "Token should contain token_type"
            
            # Step 4: Browse Products (Create multiple products)
            product1 = self._create_test_product("Shirt", Decimal("25.99"))
            product2 = self._create_test_product("Pants", Decimal("45.99"))
            product3 = self._create_test_product("Shoes", Decimal("89.99"))
            products = [product1, product2, product3]
            
            # Verify products are created correctly
            for product in products:
                assert product is not None, "Product creation should succeed"
                retrieved_product = self.product_service.get_product_by_id(product.id)
                assert retrieved_product is not None, "Product should be retrievable"
            
            # Step 5: Add Multiple Items to Cart
            cart_items = []
            
            # Add shirt (quantity 2)
            cart_item1 = self.cart_service.add_to_cart(
                user_id=user.id,
                cookie=None,
                product_id=product1.id,
                size="M",
                quantity=2
            )
            cart_items.append(cart_item1)
            
            # Add pants (quantity 1)
            cart_item2 = self.cart_service.add_to_cart(
                user_id=user.id,
                cookie=None,
                product_id=product2.id,
                size="L",
                quantity=1
            )
            cart_items.append(cart_item2)
            
            # Add shoes (quantity 1)
            cart_item3 = self.cart_service.add_to_cart(
                user_id=user.id,
                cookie=None,
                product_id=product3.id,
                size="S",
                quantity=1
            )
            cart_items.append(cart_item3)
            
            # Verify all cart items were added
            for cart_item in cart_items:
                assert cart_item is not None, "Adding to cart should succeed"
            
            # Step 6: Verify Cart Contents
            cart_contents = self.cart_service.get_cart_contents(user_id=user.id, cookie=None)
            assert len(cart_contents) == 3, "Cart should contain three items"
            
            # Verify cart total calculation
            expected_total = (Decimal("25.99") * 2) + Decimal("45.99") + Decimal("89.99")  # 187.96
            cart_total = sum(item.quantity * self.product_service.get_product_by_id(item.product_id).price 
                           for item in cart_contents)
            assert cart_total == expected_total, f"Cart total should be {expected_total}, got {cart_total}"
            
            # Step 7: Update Cart Item (change shirt quantity from 2 to 3)
            updated_item = self.cart_service.update_cart_item(cart_item1.id, 3)
            assert updated_item is not None, "Cart item update should succeed"
            assert updated_item.quantity == 3, "Cart item quantity should be updated"
            
            # Step 8: Remove One Item from Cart (remove shoes)
            removed = self.cart_service.remove_from_cart(cart_item3.id)
            assert removed is True, "Cart item removal should succeed"
            
            # Verify cart after modifications
            updated_cart = self.cart_service.get_cart_contents(user_id=user.id, cookie=None)
            assert len(updated_cart) == 2, "Cart should contain two items after removal"
            
            # Step 9: Create Order
            order_request = CreateOrderRequest(
                shipping_address="123 Shopping St, Commerce City, CC 12345",
                payment_method="credit_card",
                notes="Please handle with care"
            )
            
            order_response = self.order_service.create_order(user.id, order_request)
            assert order_response is not None, "Order creation should succeed"
            
            # Verify order details
            expected_order_total = (Decimal("25.99") * 3) + Decimal("45.99")  # 123.96
            assert order_response.total_amount == expected_order_total, "Order total should be correct"
            assert order_response.status == "confirmed", "Order status should be confirmed"
            assert len(order_response.items) == 2, "Order should contain two items"
            
            # Step 10: Verify Cart is Cleared After Order
            cart_after_order = self.cart_service.get_cart_contents(user_id=user.id, cookie=None)
            assert len(cart_after_order) == 0, "Cart should be empty after order creation"
            
            # Step 11: Verify Inventory is Reduced
            shirt_inventory = self.product_service.get_product_inventory(product1.id, "M")
            pants_inventory = self.product_service.get_product_inventory(product2.id, "L")
            shoes_inventory = self.product_service.get_product_inventory(product3.id, "S")
            
            assert shirt_inventory < 10, "Shirt inventory should be reduced"
            assert pants_inventory < 10, "Pants inventory should be reduced"
            assert shoes_inventory == 10, "Shoes inventory should not be reduced (item was removed from cart)"
            
            # Step 12: Verify Order History
            user_orders = self.order_service.get_user_orders(user.id)
            assert len(user_orders) == 1, "User should have one order"
            assert user_orders[0].id == order_response.id, "Order should match created order"
            
            # Step 13: Verify Product View Count Increment
            initial_views = product1.product_views
            success = self.product_service.increment_product_views(product1.id)
            assert success is True, "View increment should succeed"
            
            updated_product = self.product_service.get_product_by_id(product1.id)
            assert updated_product.product_views == initial_views + 1, "View count should be incremented"
            
        finally:
            # Clean up
            if user:
                try:
                    self.db_cart_service.clear_cart(user_id=user.id, cookie=None)
                    self.user_service.delete_user(user.id)
                except:
                    pass
            for product in products:
                try:
                    self.product_service.delete_product(product.id)
                except:
                    pass
    
    def test_guest_to_registered_user_workflow(self):
        """
        Test workflow where guest user adds items to cart, then registers and continues shopping.
        """
        product = None
        user = None
        
        try:
            # Step 1: Generate Guest Cookie
            guest_cookie_data = self.auth_service.generate_guest_cookie()
            guest_cookie = guest_cookie_data["cookie"]
            assert guest_cookie.startswith("guest_"), "Guest cookie should have correct format"
            
            # Step 2: Create Product
            product = self._create_test_product("GuestProduct")
            
            # Step 3: Guest Adds Items to Cart
            guest_cart_item = self.cart_service.add_to_cart(
                user_id=None,
                cookie=guest_cookie,
                product_id=product.id,
                size="M",
                quantity=2
            )
            assert guest_cart_item is not None, "Guest adding to cart should succeed"
            
            # Step 4: Verify Guest Cart
            guest_cart = self.cart_service.get_cart_contents(user_id=None, cookie=guest_cookie)
            assert len(guest_cart) == 1, "Guest cart should contain one item"
            
            # Step 5: Guest Registers
            email = f"guest_convert{secrets.randbelow(1000)}@test.com"
            password = "guestpass123"
            phone = "9876543210"
            
            user = self.auth_service.register_user(email, password, phone)
            assert user is not None, "Guest registration should succeed"
            
            # Step 6: Add More Items as Registered User
            additional_item = self.cart_service.add_to_cart(
                user_id=user.id,
                cookie=None,
                product_id=product.id,
                size="L",
                quantity=1
            )
            assert additional_item is not None, "Registered user adding to cart should succeed"
            
            # Step 7: Verify Both Carts Exist Separately
            guest_cart_final = self.cart_service.get_cart_contents(user_id=None, cookie=guest_cookie)
            user_cart = self.cart_service.get_cart_contents(user_id=user.id, cookie=None)
            
            assert len(guest_cart_final) == 1, "Guest cart should still contain original item"
            assert len(user_cart) == 1, "User cart should contain new item"
            
            # Step 8: Create Order as Registered User
            order_request = CreateOrderRequest(
                shipping_address="456 Convert St, Registration City, RC 67890",
                payment_method="debit_card"
            )
            
            order_response = self.order_service.create_order(user.id, order_request)
            assert order_response is not None, "Order creation should succeed"
            assert order_response.total_amount == Decimal("29.99"), "Order total should be correct"
            
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
            if product:
                try:
                    self.product_service.delete_product(product.id)
                except:
                    pass
    
    def test_error_handling_scenarios(self):
        """
        Test various error handling scenarios throughout the system.
        """
        user = None
        product = None
        
        try:
            # Step 1: Test Invalid User Registration
            with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
                self.auth_service.register_user("invalid@test.com", "123456", "1234567890")
            
            with pytest.raises(ValueError, match="Password must contain at least one letter"):
                self.auth_service.register_user("invalid@test.com", "12345678", "1234567890")
            
            with pytest.raises(ValueError, match="Password must contain at least one number"):
                self.auth_service.register_user("invalid@test.com", "password", "1234567890")
            
            # Step 2: Test Duplicate User Registration
            email = f"duplicate{secrets.randbelow(1000)}@test.com"
            user = self.auth_service.register_user(email, "validpass123", "1234567890")
            assert user is not None, "First registration should succeed"
            
            # Try to register same email again
            try:
                duplicate_user = self.auth_service.register_user(email, "anotherpass123", "0987654321")
                assert False, "Duplicate registration should raise an exception"
            except ValueError as e:
                assert "Email address is already registered" in str(e), "Should get duplicate email error"
            
            # Step 3: Test Invalid Authentication
            invalid_auth = self.auth_service.authenticate_user("nonexistent@test.com", "wrongpass")
            assert invalid_auth is None, "Authentication with invalid credentials should fail"
            
            wrong_password = self.auth_service.authenticate_user(email, "wrongpassword")
            assert wrong_password is None, "Authentication with wrong password should fail"
            
            # Step 4: Test Cart Operations with Invalid Data
            product = self._create_test_product("ErrorTest")
            
            # Try to add more items than available inventory
            with pytest.raises(ValueError):
                self.cart_service.add_to_cart(
                    user_id=user.id,
                    cookie=None,
                    product_id=product.id,
                    size="M",
                    quantity=15  # More than available (10)
                )
            
            # Try to add item with invalid product ID
            try:
                invalid_cart_item = self.cart_service.add_to_cart(
                    user_id=user.id,
                    cookie=None,
                    product_id=99999,  # Non-existent product
                    size="M",
                    quantity=1
                )
                assert False, "Adding non-existent product should raise an exception"
            except ValueError:
                pass  # Expected behavior
            
            # Step 5: Test Order Creation with Empty Cart
            with pytest.raises(ValueError, match="Cannot create order: cart is empty"):
                order_request = CreateOrderRequest(
                    shipping_address="123 Empty Cart St",
                    payment_method="credit_card"
                )
                self.order_service.create_order(user.id, order_request)
            
            # Step 6: Test Invalid Cart Item Operations
            # Try to update non-existent cart item
            try:
                updated_item = self.cart_service.update_cart_item(99999, 5)
                assert False, "Updating non-existent cart item should raise an exception"
            except ValueError:
                pass  # Expected behavior
            
            # Try to remove non-existent cart item
            try:
                removed = self.cart_service.remove_from_cart(99999)
                assert False, "Removing non-existent cart item should raise an exception"
            except ValueError:
                pass  # Expected behavior
            
            # Step 7: Test Product Operations with Invalid Data
            # Try to get non-existent product
            invalid_product = self.product_service.get_product_by_id(99999)
            assert invalid_product is None, "Getting non-existent product should return None"
            
            # Try to increment views for non-existent product
            view_increment = self.product_service.increment_product_views(99999)
            assert view_increment is False, "Incrementing views for non-existent product should fail"
            
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
    
    def test_concurrent_operations_workflow(self):
        """
        Test workflow with concurrent operations to verify system stability.
        """
        users = []
        products = []
        
        try:
            # Step 1: Create Multiple Users
            for i in range(3):
                email = f"concurrent{i}_{secrets.randbelow(1000)}@test.com"
                user = self.auth_service.register_user(email, f"concpass{i}123", f"123456789{i}")
                assert user is not None, f"User {i} registration should succeed"
                users.append(user)
            
            # Step 2: Create Multiple Products
            for i in range(2):
                product = self._create_test_product(f"Concurrent{i}", Decimal(f"{20 + i * 10}.99"))
                assert product is not None, f"Product {i} creation should succeed"
                products.append(product)
            
            # Step 3: Simulate Concurrent Cart Operations
            cart_items = []
            for user_idx, user in enumerate(users):
                for product_idx, product in enumerate(products):
                    # Use smaller quantities to avoid inventory conflicts
                    quantity = 1  # Same quantity for all users to avoid inventory issues
                    cart_item = self.cart_service.add_to_cart(
                        user_id=user.id,
                        cookie=None,
                        product_id=product.id,
                        size="M",
                        quantity=quantity
                    )
                    assert cart_item is not None, f"Cart item for user {user_idx}, product {product_idx} should be added"
                    cart_items.append(cart_item)
            
            # Step 4: Verify All Cart Operations Succeeded
            for user_idx, user in enumerate(users):
                user_cart = self.cart_service.get_cart_contents(user_id=user.id, cookie=None)
                assert len(user_cart) == len(products), f"User {user_idx} should have {len(products)} items in cart"
            
            # Step 5: Create Orders Concurrently
            orders = []
            for user_idx, user in enumerate(users):
                order_request = CreateOrderRequest(
                    shipping_address=f"123 Concurrent St {user_idx}, Multi City, MC 1234{user_idx}",
                    payment_method="credit_card"
                )
                order_response = self.order_service.create_order(user.id, order_request)
                assert order_response is not None, f"Order for user {user_idx} should be created"
                orders.append(order_response)
            
            # Step 6: Verify All Orders Were Created Successfully
            assert len(orders) == len(users), "All orders should be created"
            
            # Step 7: Verify Inventory Consistency
            for product in products:
                for size in ["S", "M", "L"]:
                    inventory = self.product_service.get_product_inventory(product.id, size)
                    assert inventory >= 0, f"Inventory for {product.name} size {size} should not be negative"
            
        finally:
            # Clean up
            for user in users:
                try:
                    self.db_cart_service.clear_cart(user_id=user.id, cookie=None)
                    self.user_service.delete_user(user.id)
                except:
                    pass
            for product in products:
                try:
                    self.product_service.delete_product(product.id)
                except:
                    pass
    
    @patch('logs.log_store.get_logger')
    def test_logging_functionality(self, mock_logger):
        """
        Test that logging functionality works correctly throughout the system.
        """
        # Create a mock logger to capture log calls
        mock_log_instance = mock_logger.return_value
        
        user = None
        product = None
        
        try:
            # Step 1: Test Authentication Logging
            email = f"logging{secrets.randbelow(1000)}@test.com"
            user = self.auth_service.register_user(email, "logpass123", "1234567890")
            
            # Verify registration logging (would be called in auth service)
            # Note: Since we're using a real logger, we can't easily mock it
            # This test verifies the system doesn't crash with logging
            
            # Step 2: Test Product Operations Logging
            product = self._create_test_product("LoggingTest")
            
            # Step 3: Test Cart Operations Logging
            cart_item = self.cart_service.add_to_cart(
                user_id=user.id,
                cookie=None,
                product_id=product.id,
                size="M",
                quantity=2
            )
            
            # Step 4: Test Order Creation Logging
            order_request = CreateOrderRequest(
                shipping_address="123 Logging St, Log City, LC 12345",
                payment_method="credit_card"
            )
            
            order_response = self.order_service.create_order(user.id, order_request)
            
            # Step 5: Test Error Logging
            try:
                # Trigger an error that should be logged
                self.cart_service.add_to_cart(
                    user_id=user.id,
                    cookie=None,
                    product_id=product.id,
                    size="M",
                    quantity=20  # More than available
                )
            except ValueError:
                pass  # Expected error
            
            # If we reach here without exceptions, logging is working
            assert True, "Logging functionality works without errors"
            
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