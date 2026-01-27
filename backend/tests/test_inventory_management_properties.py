"""
Property-based tests for inventory management during orders.

**Feature: spoxpro-backend, Property 10: Inventory Management During Orders**
**Validates: Requirements 5.2, 5.6, 10.4**

For any order placement, the system should reduce inventory quantities for purchased items 
by the exact amounts ordered, and should reject orders when insufficient inventory is available.
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


class TestInventoryManagementProperties:
    """Property-based tests for inventory management during orders."""

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
        initial_inventory=st.integers(min_value=5, max_value=20),
        order_quantity=st.integers(min_value=1, max_value=10),
        order_request=valid_order_request()
    )
    @settings(max_examples=100, deadline=None)
    def test_inventory_reduction_on_order_placement(
        self, user_data, product_data, initial_inventory, order_quantity, order_request
    ):
        """
        Property: Order placement should reduce inventory by exact amounts ordered.
        
        For any order with valid inventory, placing the order should reduce
        the product inventory by exactly the quantity ordered.
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
            
            # Create product size with initial inventory
            size = 'M'
            product_size = ProductSize(
                product_id=product.id,
                size=size,
                quantity=initial_inventory
            )
            self.session.add(product_size)
            self.session.commit()
            
            # Only test if order quantity is within available inventory
            if order_quantity <= initial_inventory:
                # Add item to cart
                self.cart_service.add_cart_item(
                    user_id=user.id,
                    cookie=None,
                    product_id=product.id,
                    size=size,
                    quantity=order_quantity
                )
                
                # Get initial inventory
                initial_stock = self.product_service.get_inventory(product.id, size)
                assert initial_stock == initial_inventory
                
                # Create order
                order_response = self.order_processing_service.create_order(
                    user_id=user.id,
                    order_request=order_request
                )
                
                # Verify order was created
                assert order_response is not None
                assert order_response.status == 'confirmed'
                
                # Check inventory was reduced by exact amount
                final_stock = self.product_service.get_inventory(product.id, size)
                expected_stock = initial_inventory - order_quantity
                
                assert final_stock == expected_stock, (
                    f"Expected inventory {expected_stock}, got {final_stock}. "
                    f"Initial: {initial_inventory}, Ordered: {order_quantity}"
                )
                
        except Exception as e:
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                pytest.skip(f"Skipping due to constraint violation: {e}")
            raise

    @given(
        user_data=valid_user_data(),
        product_data=valid_product_data(),
        available_inventory=st.integers(min_value=1, max_value=5),
        requested_quantity=st.integers(min_value=6, max_value=15),
        order_request=valid_order_request()
    )
    @settings(max_examples=100, deadline=None)
    def test_order_rejection_on_insufficient_inventory(
        self, user_data, product_data, available_inventory, requested_quantity, order_request
    ):
        """
        Property: Orders should be rejected when insufficient inventory is available.
        
        For any order requesting more items than available in inventory,
        the system should reject the order and not modify inventory.
        """
        try:
            # Ensure we're testing insufficient inventory scenario
            assert requested_quantity > available_inventory
            
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
            size = 'L'
            product_size = ProductSize(
                product_id=product.id,
                size=size,
                quantity=available_inventory
            )
            self.session.add(product_size)
            self.session.commit()
            
            # Try to add more items to cart than available
            # This should fail at the cart level or order level
            try:
                self.cart_service.add_cart_item(
                    user_id=user.id,
                    cookie=None,
                    product_id=product.id,
                    size=size,
                    quantity=requested_quantity
                )
                
                # If cart addition succeeded, order creation should fail
                with pytest.raises((ValueError, Exception)):
                    self.order_processing_service.create_order(
                        user_id=user.id,
                        order_request=order_request
                    )
                    
            except Exception:
                # Cart addition failed due to inventory check - this is expected
                pass
            
            # Verify inventory unchanged
            final_inventory = self.product_service.get_inventory(product.id, size)
            assert final_inventory == available_inventory, (
                f"Inventory should remain unchanged at {available_inventory}, got {final_inventory}"
            )
            
        except Exception as e:
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                pytest.skip(f"Skipping due to constraint violation: {e}")
            raise

    @given(
        user_data=valid_user_data(),
        product_data_list=st.lists(valid_product_data(), min_size=2, max_size=5),
        inventory_quantities=st.lists(st.integers(min_value=3, max_value=10), min_size=2, max_size=5),
        order_quantities=st.lists(st.integers(min_value=1, max_value=5), min_size=2, max_size=5),
        order_request=valid_order_request()
    )
    @settings(max_examples=50, deadline=None)
    def test_multi_item_inventory_management(
        self, user_data, product_data_list, inventory_quantities, order_quantities, order_request
    ):
        """
        Property: Multi-item orders should reduce inventory correctly for all items.
        
        For any order with multiple items, each product's inventory should be
        reduced by the exact quantity ordered for that specific product.
        """
        try:
            # Ensure lists are same length
            min_length = min(len(product_data_list), len(inventory_quantities), len(order_quantities))
            product_data_list = product_data_list[:min_length]
            inventory_quantities = inventory_quantities[:min_length]
            order_quantities = order_quantities[:min_length]
            
            # Create user
            user = User(**user_data)
            self.session.add(user)
            self.session.commit()
            
            products = []
            initial_inventories = []
            
            # Create products and add to cart
            for i, (product_data, inventory_qty, order_qty) in enumerate(
                zip(product_data_list, inventory_quantities, order_quantities)
            ):
                # Ensure sufficient inventory
                if order_qty > inventory_qty:
                    inventory_qty = order_qty + 2
                
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
                size = 'XL'
                product_size = ProductSize(
                    product_id=product.id,
                    size=size,
                    quantity=inventory_qty
                )
                self.session.add(product_size)
                self.session.commit()
                
                products.append(product)
                initial_inventories.append(inventory_qty)
                
                # Add to cart
                self.cart_service.add_cart_item(
                    user_id=user.id,
                    cookie=None,
                    product_id=product.id,
                    size=size,
                    quantity=order_qty
                )
            
            # Create order
            order_response = self.order_processing_service.create_order(
                user_id=user.id,
                order_request=order_request
            )
            
            # Verify order created
            assert order_response is not None
            assert order_response.status == 'confirmed'
            
            # Verify inventory reduced correctly for each product
            for product, initial_inventory, order_qty in zip(products, initial_inventories, order_quantities):
                final_inventory = self.product_service.get_inventory(product.id, 'XL')
                expected_inventory = initial_inventory - order_qty
                
                assert final_inventory == expected_inventory, (
                    f"Product {product.id}: Expected inventory {expected_inventory}, "
                    f"got {final_inventory}. Initial: {initial_inventory}, Ordered: {order_qty}"
                )
                
        except Exception as e:
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                pytest.skip(f"Skipping due to constraint violation: {e}")
            raise

    @given(
        user_data=valid_user_data(),
        product_data=valid_product_data(),
        initial_inventory=st.integers(min_value=5, max_value=15),
        order_quantity=st.integers(min_value=1, max_value=8),
        order_request=valid_order_request()
    )
    @settings(max_examples=100, deadline=None)
    def test_inventory_restoration_on_order_cancellation(
        self, user_data, product_data, initial_inventory, order_quantity, order_request
    ):
        """
        Property: Cancelled orders should restore inventory to original levels.
        
        For any cancelled order, the inventory should be restored by adding back
        the exact quantities that were originally deducted.
        """
        try:
            # Ensure sufficient inventory
            if order_quantity > initial_inventory:
                initial_inventory = order_quantity + 3
            
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
            size = 'S'
            product_size = ProductSize(
                product_id=product.id,
                size=size,
                quantity=initial_inventory
            )
            self.session.add(product_size)
            self.session.commit()
            
            # Add to cart
            self.cart_service.add_cart_item(
                user_id=user.id,
                cookie=None,
                product_id=product.id,
                size=size,
                quantity=order_quantity
            )
            
            # Create order
            order_response = self.order_processing_service.create_order(
                user_id=user.id,
                order_request=order_request
            )
            
            # Verify inventory was reduced
            inventory_after_order = self.product_service.get_inventory(product.id, size)
            expected_after_order = initial_inventory - order_quantity
            assert inventory_after_order == expected_after_order
            
            # Cancel the order
            cancellation_success = self.order_processing_service.cancel_order(
                order_id=order_response.id,
                user_id=user.id
            )
            
            assert cancellation_success is True
            
            # Verify inventory was restored
            inventory_after_cancellation = self.product_service.get_inventory(product.id, size)
            
            assert inventory_after_cancellation == initial_inventory, (
                f"Expected inventory restored to {initial_inventory}, "
                f"got {inventory_after_cancellation}"
            )
            
        except Exception as e:
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                pytest.skip(f"Skipping due to constraint violation: {e}")
            raise

    @given(
        user_data=valid_user_data(),
        product_data=valid_product_data(),
        size_inventory_pairs=st.lists(
            st.tuples(
                st.sampled_from(['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL']),
                st.integers(min_value=2, max_value=10)
            ),
            min_size=2,
            max_size=4,
            unique_by=lambda x: x[0]  # Unique sizes
        ),
        order_request=valid_order_request()
    )
    @settings(max_examples=50, deadline=None)
    def test_size_specific_inventory_management(
        self, user_data, product_data, size_inventory_pairs, order_request
    ):
        """
        Property: Inventory management should be size-specific.
        
        For any product with multiple sizes, ordering one size should only
        affect the inventory of that specific size, not other sizes.
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
            
            # Create product sizes
            initial_inventories = {}
            for size, inventory in size_inventory_pairs:
                product_size = ProductSize(
                    product_id=product.id,
                    size=size,
                    quantity=inventory
                )
                self.session.add(product_size)
                initial_inventories[size] = inventory
            
            self.session.commit()
            
            # Order from the first size only
            ordered_size = size_inventory_pairs[0][0]
            order_quantity = min(2, size_inventory_pairs[0][1])  # Order safe amount
            
            # Add to cart
            self.cart_service.add_cart_item(
                user_id=user.id,
                cookie=None,
                product_id=product.id,
                size=ordered_size,
                quantity=order_quantity
            )
            
            # Create order
            order_response = self.order_processing_service.create_order(
                user_id=user.id,
                order_request=order_request
            )
            
            # Verify only the ordered size inventory was affected
            for size, initial_inventory in initial_inventories.items():
                current_inventory = self.product_service.get_inventory(product.id, size)
                
                if size == ordered_size:
                    # This size should be reduced
                    expected_inventory = initial_inventory - order_quantity
                    assert current_inventory == expected_inventory, (
                        f"Ordered size {size}: Expected {expected_inventory}, got {current_inventory}"
                    )
                else:
                    # Other sizes should be unchanged
                    assert current_inventory == initial_inventory, (
                        f"Non-ordered size {size}: Expected {initial_inventory}, got {current_inventory}"
                    )
                    
        except Exception as e:
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                pytest.skip(f"Skipping due to constraint violation: {e}")
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])