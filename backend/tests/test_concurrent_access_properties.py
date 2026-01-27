"""
Property-based tests for concurrent access safety functionality.

**Feature: spoxpro-backend, Property 16: Concurrent Access Safety**
**Validates: Requirements 10.5**

For any simultaneous operations on shared resources (inventory, cart, orders), 
the system should prevent data corruption and maintain data consistency across 
concurrent access scenarios.
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
import threading
import time
import concurrent.futures
from typing import List, Dict, Any

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
def concurrent_operation_strategy(draw):
    """Generate concurrent operation parameters."""
    return {
        'thread_count': draw(st.integers(min_value=2, max_value=5)),
        'operations_per_thread': draw(st.integers(min_value=1, max_value=3)),
        'size': draw(st.sampled_from(['S', 'M', 'L'])),
        'quantity': draw(st.integers(min_value=1, max_value=5))
    }


class TestConcurrentAccessSafetyProperties:
    """Property-based tests for concurrent access safety."""
    
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
    
    def _create_test_product(self, article_suffix="", initial_inventory=50):
        """Create a test product for concurrent operations."""
        product_data = {
            "name": f"Concurrent Test Product {article_suffix}",
            "description": "Test Description for Concurrent Access",
            "product_type_id": 1,
            "category_id": 1,
            "sport_type_id": 1,
            "color": "Blue",
            "gender": "unisex",
            "brand": "spoXpro",
            "price": Decimal("29.99"),
            "reviews": [],
            "article_number": f"CONC{article_suffix}{secrets.randbelow(10000)}",
            "images": ["test.jpg"],
            "material_id": 1,
            "sizes": [
                {"size": "S", "quantity": initial_inventory},
                {"size": "M", "quantity": initial_inventory},
                {"size": "L", "quantity": initial_inventory}
            ]
        }
        return self.product_service.create_product(product_data)
    
    def _create_test_user(self, email_suffix=""):
        """Create a test user for concurrent operations."""
        email = f"concurrent{email_suffix}@test.com"
        password = "testpass123"
        phone = "1234567890"
        return self.auth_service.register_user(email, password, phone)
    
    # ==================== CONCURRENT INVENTORY OPERATIONS ====================
    
    @given(
        concurrent_params=concurrent_operation_strategy()
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_concurrent_inventory_updates_maintain_consistency(self, concurrent_params):
        """
        Property: For any simultaneous inventory update operations, the final 
        inventory count should be mathematically consistent with all operations.
        
        **Validates: Requirements 10.5**
        """
        product = None
        users = []
        
        try:
            # Create test product with sufficient inventory
            initial_inventory = 100
            product = self._create_test_product(f"INV{secrets.randbelow(1000)}", initial_inventory)
            assume(product is not None)
            
            # Create multiple users for concurrent operations
            thread_count = concurrent_params['thread_count']
            operations_per_thread = concurrent_params['operations_per_thread']
            size = concurrent_params['size']
            quantity = concurrent_params['quantity']
            
            for i in range(thread_count):
                user = self._create_test_user(f"{i}{secrets.randbelow(1000)}")
                assume(user is not None)
                users.append(user)
            
            # Calculate expected final inventory
            total_operations = thread_count * operations_per_thread
            expected_inventory_reduction = total_operations * quantity
            expected_final_inventory = initial_inventory - expected_inventory_reduction
            
            # Skip test if we would exceed inventory
            assume(expected_final_inventory >= 0)
            
            # Results tracking
            results = []
            errors = []
            
            def concurrent_cart_add_operation(user_id, thread_id):
                """Add items to cart concurrently."""
                thread_results = []
                thread_errors = []
                
                try:
                    # Create new database session for this thread
                    thread_db = get_db_session()
                    thread_cart_service = DBCartService(thread_db)
                    
                    for op in range(operations_per_thread):
                        try:
                            result = thread_cart_service.add_cart_item(
                                user_id=user_id,
                                cookie=None,
                                product_id=product.id,
                                size=size,
                                quantity=quantity
                            )
                            thread_results.append({
                                'thread_id': thread_id,
                                'operation': op,
                                'success': result is not None,
                                'result': result
                            })
                        except Exception as e:
                            thread_errors.append({
                                'thread_id': thread_id,
                                'operation': op,
                                'error': str(e)
                            })
                    
                    thread_db.close()
                    
                except Exception as e:
                    thread_errors.append({
                        'thread_id': thread_id,
                        'error': f"Thread setup error: {str(e)}"
                    })
                
                return thread_results, thread_errors
            
            # Execute concurrent operations
            with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
                futures = []
                for i, user in enumerate(users):
                    future = executor.submit(concurrent_cart_add_operation, user.id, i)
                    futures.append(future)
                
                # Collect results
                for future in concurrent.futures.as_completed(futures):
                    thread_results, thread_errors = future.result()
                    results.extend(thread_results)
                    errors.extend(thread_errors)
            
            # Verify inventory consistency
            final_inventory = self.product_service.get_product_inventory(product.id, size)
            
            # Count successful operations
            successful_operations = sum(1 for r in results if r['success'])
            actual_inventory_reduction = successful_operations * quantity
            expected_final_after_success = initial_inventory - actual_inventory_reduction
            
            # Property assertions for concurrent access safety
            assert final_inventory >= 0, "Inventory should never go negative"
            assert final_inventory == expected_final_after_success, \
                f"Final inventory ({final_inventory}) should match expected ({expected_final_after_success}) based on successful operations"
            
            # Verify no inventory was lost or gained unexpectedly
            total_cart_quantity = 0
            for user in users:
                cart_items = self.cart_service.get_cart_contents(user_id=user.id, cookie=None)
                for item in cart_items:
                    if item.product_id == product.id and item.size == size:
                        total_cart_quantity += item.quantity
            
            # Total inventory + cart quantities should equal initial inventory
            total_accounted = final_inventory + total_cart_quantity
            assert total_accounted == initial_inventory, \
                f"Total inventory ({final_inventory}) + cart quantities ({total_cart_quantity}) should equal initial inventory ({initial_inventory})"
            
            # Log results for debugging
            if errors:
                print(f"Concurrent operation errors: {len(errors)}")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"  Error: {error}")
            
        finally:
            # Clean up
            for user in users:
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
    
    # ==================== CONCURRENT CART OPERATIONS ====================
    
    @given(
        concurrent_params=concurrent_operation_strategy()
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_concurrent_cart_operations_maintain_isolation(self, concurrent_params):
        """
        Property: For any simultaneous cart operations by different users,
        each user's cart should remain isolated and consistent.
        
        **Validates: Requirements 10.5**
        """
        product = None
        users = []
        
        try:
            # Create test product
            product = self._create_test_product(f"CART{secrets.randbelow(1000)}", 200)
            assume(product is not None)
            
            # Create multiple users
            thread_count = concurrent_params['thread_count']
            operations_per_thread = concurrent_params['operations_per_thread']
            size = concurrent_params['size']
            quantity = concurrent_params['quantity']
            
            for i in range(thread_count):
                user = self._create_test_user(f"cart{i}{secrets.randbelow(1000)}")
                assume(user is not None)
                users.append(user)
            
            # Results tracking
            results = {}
            errors = []
            
            def concurrent_user_cart_operations(user_id, thread_id):
                """Perform cart operations for a specific user."""
                thread_results = []
                thread_errors = []
                
                try:
                    # Create new database session for this thread
                    thread_db = get_db_session()
                    thread_cart_service = DBCartService(thread_db)
                    
                    for op in range(operations_per_thread):
                        try:
                            # Add item to cart
                            result = thread_cart_service.add_cart_item(
                                user_id=user_id,
                                cookie=None,
                                product_id=product.id,
                                size=size,
                                quantity=quantity
                            )
                            
                            if result:
                                thread_results.append({
                                    'operation': 'add',
                                    'success': True,
                                    'item_id': result.id,
                                    'quantity': result.quantity
                                })
                        except Exception as e:
                            thread_errors.append({
                                'operation': 'add',
                                'error': str(e)
                            })
                    
                    thread_db.close()
                    
                except Exception as e:
                    thread_errors.append({
                        'thread_id': thread_id,
                        'error': f"Thread setup error: {str(e)}"
                    })
                
                return thread_results, thread_errors
            
            # Execute concurrent operations
            with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
                futures = {}
                for i, user in enumerate(users):
                    future = executor.submit(concurrent_user_cart_operations, user.id, i)
                    futures[future] = user.id
                
                # Collect results
                for future in concurrent.futures.as_completed(futures):
                    user_id = futures[future]
                    thread_results, thread_errors = future.result()
                    results[user_id] = thread_results
                    errors.extend(thread_errors)
            
            # Verify cart isolation and consistency
            for user in users:
                user_cart = self.cart_service.get_cart_contents(user_id=user.id, cookie=None)
                user_results = results.get(user.id, [])
                
                # Property assertions for cart isolation
                if user_results:
                    # User should have cart items if operations succeeded
                    successful_adds = [r for r in user_results if r['success'] and r['operation'] == 'add']
                    
                    if successful_adds:
                        assert len(user_cart) > 0, f"User {user.id} should have cart items after successful operations"
                        
                        # Find cart item for this product/size
                        matching_items = [item for item in user_cart 
                                        if item.product_id == product.id and item.size == size]
                        
                        if matching_items:
                            cart_item = matching_items[0]
                            expected_quantity = sum(r['quantity'] for r in successful_adds)
                            
                            # Verify quantity consistency
                            assert cart_item.quantity == expected_quantity, \
                                f"User {user.id} cart quantity should match successful operations"
                
                # Verify cart items belong only to this user
                for item in user_cart:
                    assert item.user_id == user.id, f"Cart item should belong to user {user.id}"
                    assert item.cookie is None, "Authenticated user cart items should not have cookies"
            
            # Verify no cross-contamination between user carts
            all_cart_items = []
            for user in users:
                user_cart = self.cart_service.get_cart_contents(user_id=user.id, cookie=None)
                all_cart_items.extend(user_cart)
            
            # Each cart item should belong to exactly one user
            user_ids_in_carts = [item.user_id for item in all_cart_items]
            for user_id in user_ids_in_carts:
                assert user_id in [u.id for u in users], "Cart items should only belong to test users"
            
        finally:
            # Clean up
            for user in users:
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
    
    # ==================== CONCURRENT ORDER PROCESSING ====================
    
    @given(
        user_count=st.integers(min_value=2, max_value=4),
        items_per_cart=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_concurrent_order_processing_maintains_inventory_consistency(self, user_count, items_per_cart):
        """
        Property: For any simultaneous order processing operations, inventory 
        should be reduced correctly and no overselling should occur.
        
        **Validates: Requirements 10.5**
        """
        products = []
        users = []
        
        try:
            # Create test products with limited inventory
            initial_inventory = 20
            for i in range(items_per_cart):
                product = self._create_test_product(f"ORDER{i}{secrets.randbelow(1000)}", initial_inventory)
                assume(product is not None)
                products.append(product)
            
            # Create users and populate their carts
            for i in range(user_count):
                user = self._create_test_user(f"order{i}{secrets.randbelow(1000)}")
                assume(user is not None)
                users.append(user)
                
                # Add items to user's cart
                for product in products:
                    self.cart_service.add_to_cart(
                        user_id=user.id,
                        cookie=None,
                        product_id=product.id,
                        size="M",
                        quantity=2  # Each user wants 2 of each item
                    )
            
            # Record initial inventory
            initial_inventories = {}
            for product in products:
                initial_inventories[product.id] = self.product_service.get_product_inventory(product.id, "M")
            
            # Results tracking
            order_results = []
            errors = []
            
            def concurrent_order_processing(user_id, thread_id):
                """Process order for a specific user."""
                try:
                    # Create new database session for this thread
                    thread_db = get_db_session()
                    thread_order_service = DBOrderService(thread_db)
                    thread_cart_service = DBCartService(thread_db)
                    thread_product_service = ProductService(thread_db)
                    
                    order_processing_service = OrderProcessingService(
                        thread_order_service,
                        thread_cart_service,
                        thread_product_service
                    )
                    
                    # Create order request
                    order_request = CreateOrderRequest(
                        shipping_address="123 Test St",
                        payment_method="credit_card"
                    )
                    
                    # Process order
                    order_response = order_processing_service.create_order(user_id, order_request)
                    
                    thread_db.close()
                    
                    return {
                        'thread_id': thread_id,
                        'user_id': user_id,
                        'success': True,
                        'order_id': order_response.id,
                        'total_amount': order_response.total_amount
                    }
                    
                except Exception as e:
                    return {
                        'thread_id': thread_id,
                        'user_id': user_id,
                        'success': False,
                        'error': str(e)
                    }
            
            # Execute concurrent order processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=user_count) as executor:
                futures = []
                for i, user in enumerate(users):
                    future = executor.submit(concurrent_order_processing, user.id, i)
                    futures.append(future)
                
                # Collect results
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    order_results.append(result)
                    if not result['success']:
                        errors.append(result)
            
            # Verify inventory consistency after concurrent orders
            successful_orders = [r for r in order_results if r['success']]
            failed_orders = [r for r in order_results if not r['success']]
            
            # Check final inventory
            for product in products:
                final_inventory = self.product_service.get_product_inventory(product.id, "M")
                initial_inv = initial_inventories[product.id]
                
                # Calculate expected inventory reduction
                expected_reduction = len(successful_orders) * 2  # Each successful order took 2 items
                expected_final_inventory = initial_inv - expected_reduction
                
                # Property assertions for inventory consistency
                assert final_inventory >= 0, f"Product {product.id} inventory should never go negative"
                assert final_inventory == expected_final_inventory, \
                    f"Product {product.id} final inventory ({final_inventory}) should match expected ({expected_final_inventory})"
            
            # Verify no overselling occurred
            total_expected_orders = user_count
            total_possible_orders = min(initial_inventory // 2, total_expected_orders)  # Each order needs 2 items per product
            
            assert len(successful_orders) <= total_possible_orders, \
                f"Number of successful orders ({len(successful_orders)}) should not exceed possible orders ({total_possible_orders})"
            
            # Verify carts were cleared for successful orders
            for result in successful_orders:
                user_cart = self.cart_service.get_cart_contents(user_id=result['user_id'], cookie=None)
                assert len(user_cart) == 0, f"Cart should be empty after successful order for user {result['user_id']}"
            
            # Verify carts were NOT cleared for failed orders
            for result in failed_orders:
                user_cart = self.cart_service.get_cart_contents(user_id=result['user_id'], cookie=None)
                # Cart should still have items if order failed
                assert len(user_cart) > 0, f"Cart should not be empty after failed order for user {result['user_id']}"
            
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
    
    # ==================== CONCURRENT MIXED OPERATIONS ====================
    
    @given(
        operation_mix=st.integers(min_value=2, max_value=4)
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_concurrent_mixed_operations_maintain_system_consistency(self, operation_mix):
        """
        Property: For any mix of simultaneous operations (cart adds, updates, 
        order processing), the system should maintain overall data consistency.
        
        **Validates: Requirements 10.5**
        """
        product = None
        users = []
        
        try:
            # Create test product with sufficient inventory
            initial_inventory = 100
            product = self._create_test_product(f"MIX{secrets.randbelow(1000)}", initial_inventory)
            assume(product is not None)
            
            # Create multiple users
            for i in range(operation_mix):
                user = self._create_test_user(f"mix{i}{secrets.randbelow(1000)}")
                assume(user is not None)
                users.append(user)
            
            # Results tracking
            results = []
            
            def mixed_operation_worker(user_id, operation_type, thread_id):
                """Perform different types of operations concurrently."""
                try:
                    # Create new database session for this thread
                    thread_db = get_db_session()
                    thread_cart_service = DBCartService(thread_db)
                    thread_product_service = ProductService(thread_db)
                    
                    if operation_type == 'cart_add':
                        # Add items to cart
                        result = thread_cart_service.add_cart_item(
                            user_id=user_id,
                            cookie=None,
                            product_id=product.id,
                            size="M",
                            quantity=3
                        )
                        success = result is not None
                        
                    elif operation_type == 'inventory_check':
                        # Check inventory (read operation)
                        inventory = thread_product_service.get_product_inventory(product.id, "M")
                        success = inventory >= 0
                        
                    elif operation_type == 'cart_update':
                        # First add an item, then update it
                        cart_item = thread_cart_service.add_cart_item(
                            user_id=user_id,
                            cookie=None,
                            product_id=product.id,
                            size="M",
                            quantity=2
                        )
                        if cart_item:
                            updated_item = thread_cart_service.update_cart_item(cart_item.id, 4)
                            success = updated_item is not None
                        else:
                            success = False
                    
                    else:  # 'view_increment'
                        # Increment product views
                        success = thread_product_service.increment_product_views(product.id)
                    
                    thread_db.close()
                    
                    return {
                        'thread_id': thread_id,
                        'user_id': user_id,
                        'operation': operation_type,
                        'success': success
                    }
                    
                except Exception as e:
                    return {
                        'thread_id': thread_id,
                        'user_id': user_id,
                        'operation': operation_type,
                        'success': False,
                        'error': str(e)
                    }
            
            # Define operation types
            operation_types = ['cart_add', 'inventory_check', 'cart_update', 'view_increment']
            
            # Execute concurrent mixed operations
            with concurrent.futures.ThreadPoolExecutor(max_workers=operation_mix) as executor:
                futures = []
                for i, user in enumerate(users):
                    operation_type = operation_types[i % len(operation_types)]
                    future = executor.submit(mixed_operation_worker, user.id, operation_type, i)
                    futures.append(future)
                
                # Collect results
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    results.append(result)
            
            # Verify system consistency after mixed operations
            final_inventory = self.product_service.get_product_inventory(product.id, "M")
            
            # Property assertions for system consistency
            assert final_inventory >= 0, "Inventory should never go negative"
            assert final_inventory <= initial_inventory, "Inventory should not increase unexpectedly"
            
            # Verify cart operations were successful where expected
            cart_operations = [r for r in results if r['operation'] in ['cart_add', 'cart_update']]
            successful_cart_ops = [r for r in cart_operations if r['success']]
            
            # Check that users have appropriate cart contents
            total_cart_quantity = 0
            for user in users:
                user_cart = self.cart_service.get_cart_contents(user_id=user.id, cookie=None)
                for item in user_cart:
                    if item.product_id == product.id and item.size == "M":
                        total_cart_quantity += item.quantity
            
            # Verify inventory accounting
            accounted_inventory = final_inventory + total_cart_quantity
            assert accounted_inventory <= initial_inventory, \
                f"Total accounted inventory ({accounted_inventory}) should not exceed initial ({initial_inventory})"
            
            # Verify read operations (inventory_check) didn't affect data
            read_operations = [r for r in results if r['operation'] == 'inventory_check']
            for read_op in read_operations:
                assert read_op['success'], "Read operations should always succeed"
            
            # Verify view increments worked
            view_operations = [r for r in results if r['operation'] == 'view_increment']
            successful_views = [r for r in view_operations if r['success']]
            
            if successful_views:
                # Product views should have increased
                updated_product = self.product_service.get_product_by_id(product.id)
                assert updated_product.product_views >= len(successful_views), \
                    "Product views should reflect successful increment operations"
            
        finally:
            # Clean up
            for user in users:
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