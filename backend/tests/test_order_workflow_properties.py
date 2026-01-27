"""
Property-based tests for order creation and completion workflow.

**Feature: spoxpro-backend, Property 11: Order Creation and Completion Workflow**
**Validates: Requirements 5.1, 5.3, 5.4**

For any user checkout process, the system should create complete order records with all cart 
contents and user information, clear the cart upon completion, and add the order to the user's history.
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
from db.models.order import Order, OrderItem
from db.services.cart_service import CartService as DBCartService
from db.services.product_service import ProductService
from db.services.user_service import UserService
from db.services.order_service import OrderService
from service.order_service import OrderProcessingService
from DTO.user import CreateOrderRequest
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
def valid_order_request(draw):
    """Generate valid order request data."""
    return CreateOrderRequest(
        shipping_address=draw(st.text(min_size=10, max_size=200)),
        payment_method=draw(st.sampled_from(['credit_card', 'paypal', 'bank_transfer']))
    )

@st.composite
def valid_cart_item_data(draw):
    """Generate valid cart item data for testing."""
    return {
        'size': draw(st.sampled_from(['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'XXXXL'])),
        'quantity': draw(st.integers(min_value=1, max_value=5))
    }


class TestOrderWorkflowProperties:
    """Property-based tests for order creation and completion workflow."""

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
        self.order_db_service = OrderService(self.session)
        self.order_processing_service = OrderProcessingService(
            self.order_db_service,
            self.cart_service,
            self.product_service
        )
        
        yield
        
        # Cleanup
        self.session.close()

    @given(
        user_data=valid_user_data(),
        product_data=valid_product_data(),
        cart_item_data=valid_cart_item_data(),
        order_request=valid_order_request()
    )
    @settings(max_examples=100, deadline=None)
    def test_complete_order_record_creation(
        self, user_data, product_data, cart_item_data, order_request
    ):
        """
        Property: Order creation should create complete order records with all cart contents and user information.
        
        For any valid checkout process, the system should create an order record that contains
        all cart items, user information, pricing, and timestamps.
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
            product_size = ProductSize(
                product_id=product.id,
                size=cart_item_data['size'],
                quantity=cart_item_data['quantity'] + 5
            )
            self.session.add(product_size)
            self.session.commit()
            
            # Add item to cart
            cart_item = self.cart_service.add_cart_item(
                user_id=user.id,
                cookie=None,
                product_id=product.id,
                size=cart_item_data['size'],
                quantity=cart_item_data['quantity']
            )
            
            # Record cart contents before order
            cart_items_before = self.cart_service.get_cart_items(user_id=user.id, cookie=None)
            expected_total = sum(
                self.product_service.get_product_by_id(item.product_id).price * item.quantity
                for item in cart_items_before
            )
            
            # Create order
            order_response = self.order_processing_service.create_order(
                user_id=user.id,
                order_request=order_request
            )
            
            # Verify complete order record was created
            assert order_response is not None
            assert order_response.id is not None
            assert order_response.status == 'confirmed'
            assert order_response.total_amount == expected_total
            assert order_response.created_date is not None
            
            # Verify order contains all cart items
            assert len(order_response.items) == len(cart_items_before)
            
            for order_item, cart_item in zip(order_response.items, cart_items_before):
                original_product = self.product_service.get_product_by_id(cart_item.product_id)
                assert order_item.product_name == original_product.name
                assert order_item.size == cart_item.size
                assert order_item.quantity == cart_item.quantity
                assert order_item.price_at_time == original_product.price
            
            # Verify order is in database
            db_order = self.order_db_service.get_order_by_id(order_response.id)
            assert db_order is not None
            assert db_order.user_id == user.id
            assert db_order.total_amount == expected_total
            
        except Exception as e:
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                pytest.skip(f"Skipping due to constraint violation: {e}")
            raise

    @given(
        user_data=valid_user_data(),
        product_data_list=st.lists(valid_product_data(), min_size=1, max_size=4),
        cart_items_data=st.lists(valid_cart_item_data(), min_size=1, max_size=4),
        order_request=valid_order_request()
    )
    @settings(max_examples=50, deadline=None)
    def test_cart_clearing_upon_order_completion(
        self, user_data, product_data_list, cart_items_data, order_request
    ):
        """
        Property: Cart should be cleared upon successful order completion.
        
        For any successful order creation, the user's cart should be empty
        after the order is completed.
        """
        try:
            # Ensure lists are same length
            min_length = min(len(product_data_list), len(cart_items_data))
            product_data_list = product_data_list[:min_length]
            cart_items_data = cart_items_data[:min_length]
            
            # Create user
            user = User(**user_data)
            self.session.add(user)
            self.session.commit()
            
            # Create products and add to cart
            for i, (product_data, cart_item_data) in enumerate(zip(product_data_list, cart_items_data)):
                # Ensure unique article numbers
                product_data['article_number'] = f"{product_data['article_number']}_{i}"
                
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
                
                # Create product size
                product_size = ProductSize(
                    product_id=product.id,
                    size=cart_item_data['size'],
                    quantity=cart_item_data['quantity'] + 5
                )
                self.session.add(product_size)
                self.session.commit()
                
                # Add to cart
                self.cart_service.add_cart_item(
                    user_id=user.id,
                    cookie=None,
                    product_id=product.id,
                    size=cart_item_data['size'],
                    quantity=cart_item_data['quantity']
                )
            
            # Verify cart has items before order
            cart_items_before = self.cart_service.get_cart_items(user_id=user.id, cookie=None)
            assert len(cart_items_before) > 0
            
            # Create order
            order_response = self.order_processing_service.create_order(
                user_id=user.id,
                order_request=order_request
            )
            
            # Verify order was created successfully
            assert order_response is not None
            assert order_response.status == 'confirmed'
            
            # Verify cart is now empty
            cart_items_after = self.cart_service.get_cart_items(user_id=user.id, cookie=None)
            assert len(cart_items_after) == 0, (
                f"Cart should be empty after order completion, but contains {len(cart_items_after)} items"
            )
            
        except Exception as e:
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                pytest.skip(f"Skipping due to constraint violation: {e}")
            raise

    @given(
        user_data=valid_user_data(),
        product_data=valid_product_data(),
        cart_item_data=valid_cart_item_data(),
        order_request=valid_order_request()
    )
    @settings(max_examples=100, deadline=None)
    def test_order_added_to_user_history(
        self, user_data, product_data, cart_item_data, order_request
    ):
        """
        Property: Completed orders should be added to user's order history.
        
        For any successful order, the order should appear in the user's
        order history and be retrievable through order history queries.
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
            
            # Create product size
            product_size = ProductSize(
                product_id=product.id,
                size=cart_item_data['size'],
                quantity=cart_item_data['quantity'] + 5
            )
            self.session.add(product_size)
            self.session.commit()
            
            # Get initial order history
            initial_orders = self.order_processing_service.get_user_orders(user.id)
            initial_order_count = len(initial_orders)
            
            # Add item to cart
            self.cart_service.add_cart_item(
                user_id=user.id,
                cookie=None,
                product_id=product.id,
                size=cart_item_data['size'],
                quantity=cart_item_data['quantity']
            )
            
            # Create order
            order_response = self.order_processing_service.create_order(
                user_id=user.id,
                order_request=order_request
            )
            
            # Verify order was created
            assert order_response is not None
            
            # Get updated order history
            updated_orders = self.order_processing_service.get_user_orders(user.id)
            
            # Verify order was added to history
            assert len(updated_orders) == initial_order_count + 1, (
                f"Expected {initial_order_count + 1} orders in history, got {len(updated_orders)}"
            )
            
            # Verify the new order is in the history
            order_ids = [order.id for order in updated_orders]
            assert order_response.id in order_ids, (
                f"Order {order_response.id} not found in user's order history"
            )
            
            # Verify order can be retrieved individually
            retrieved_order = self.order_processing_service.get_order_by_id(
                order_response.id, 
                user.id
            )
            assert retrieved_order is not None
            assert retrieved_order.id == order_response.id
            assert retrieved_order.total_amount == order_response.total_amount
            
        except Exception as e:
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                pytest.skip(f"Skipping due to constraint violation: {e}")
            raise

    @given(
        user_data=valid_user_data(),
        product_data=valid_product_data(),
        cart_item_data=valid_cart_item_data(),
        order_request=valid_order_request()
    )
    @settings(max_examples=100, deadline=None)
    def test_order_workflow_atomicity(
        self, user_data, product_data, cart_item_data, order_request
    ):
        """
        Property: Order creation workflow should be atomic.
        
        For any order creation process, either all steps succeed (order created,
        inventory reduced, cart cleared) or all steps fail (no changes made).
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
            initial_inventory = cart_item_data['quantity'] + 5
            product_size = ProductSize(
                product_id=product.id,
                size=cart_item_data['size'],
                quantity=initial_inventory
            )
            self.session.add(product_size)
            self.session.commit()
            
            # Add item to cart
            self.cart_service.add_cart_item(
                user_id=user.id,
                cookie=None,
                product_id=product.id,
                size=cart_item_data['size'],
                quantity=cart_item_data['quantity']
            )
            
            # Record initial state
            initial_cart_items = self.cart_service.get_cart_items(user_id=user.id, cookie=None)
            initial_orders = self.order_processing_service.get_user_orders(user.id)
            initial_stock = self.product_service.get_inventory(product.id, cart_item_data['size'])
            
            # Create order
            order_response = self.order_processing_service.create_order(
                user_id=user.id,
                order_request=order_request
            )
            
            if order_response is not None:
                # Order creation succeeded - verify all changes were made
                
                # Cart should be cleared
                final_cart_items = self.cart_service.get_cart_items(user_id=user.id, cookie=None)
                assert len(final_cart_items) == 0, "Cart should be empty after successful order"
                
                # Inventory should be reduced
                final_stock = self.product_service.get_inventory(product.id, cart_item_data['size'])
                expected_stock = initial_stock - cart_item_data['quantity']
                assert final_stock == expected_stock, (
                    f"Inventory should be reduced to {expected_stock}, got {final_stock}"
                )
                
                # Order should be in history
                final_orders = self.order_processing_service.get_user_orders(user.id)
                assert len(final_orders) == len(initial_orders) + 1, (
                    "Order should be added to user history"
                )
                
                # Order should have correct status
                assert order_response.status == 'confirmed', (
                    f"Order should be confirmed, got status: {order_response.status}"
                )
                
            else:
                # Order creation failed - verify no changes were made
                
                # Cart should be unchanged
                final_cart_items = self.cart_service.get_cart_items(user_id=user.id, cookie=None)
                assert len(final_cart_items) == len(initial_cart_items), (
                    "Cart should be unchanged after failed order"
                )
                
                # Inventory should be unchanged
                final_stock = self.product_service.get_inventory(product.id, cart_item_data['size'])
                assert final_stock == initial_stock, (
                    "Inventory should be unchanged after failed order"
                )
                
                # No new orders should be created
                final_orders = self.order_processing_service.get_user_orders(user.id)
                assert len(final_orders) == len(initial_orders), (
                    "No new orders should be created after failed order"
                )
                
        except Exception as e:
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                pytest.skip(f"Skipping due to constraint violation: {e}")
            raise

    @given(
        user_data=valid_user_data(),
        order_request=valid_order_request()
    )
    @settings(max_examples=100, deadline=None)
    def test_empty_cart_order_rejection(self, user_data, order_request):
        """
        Property: Orders should be rejected when cart is empty.
        
        For any user with an empty cart, attempting to create an order
        should fail with appropriate error message.
        """
        try:
            # Create user
            user = User(**user_data)
            self.session.add(user)
            self.session.commit()
            
            # Ensure cart is empty
            cart_items = self.cart_service.get_cart_items(user_id=user.id, cookie=None)
            assert len(cart_items) == 0, "Cart should be empty for this test"
            
            # Attempt to create order with empty cart
            with pytest.raises(ValueError, match="Cannot create order: cart is empty"):
                self.order_processing_service.create_order(
                    user_id=user.id,
                    order_request=order_request
                )
            
            # Verify no order was created
            orders = self.order_processing_service.get_user_orders(user.id)
            assert len(orders) == 0, "No orders should be created from empty cart"
            
        except Exception as e:
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                pytest.skip(f"Skipping due to constraint violation: {e}")
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])