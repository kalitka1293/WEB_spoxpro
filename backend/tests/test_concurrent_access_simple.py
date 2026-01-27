"""
Simple property-based tests for concurrent access safety functionality.

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
from decimal import Decimal
import secrets
import threading
import time
from typing import List

from service.auth_service import AuthService
from service.cart_service import CartService as BusinessCartService
from db.services.user_service import UserService
from db.services.cart_service import CartService as DBCartService
from db.services.product_service import ProductService
from db.main import get_db_session
from config.database import Base, engine


class TestConcurrentAccessSimple:
    """Simple property-based tests for concurrent access safety."""
    
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
    
    def _create_test_product(self, article_suffix="", initial_inventory=50):
        """Create a test product for concurrent operations."""
        product_data = {
            "name": f"Concurrent Test Product {article_suffix}",
            "description": "Test Description",
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
    
    @given(
        thread_count=st.integers(min_value=2, max_value=3),
        quantity=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_concurrent_cart_operations_simple(self, thread_count, quantity):
        """
        Property: For any simultaneous cart operations by different users,
        each user's cart should remain isolated and inventory should be consistent.
        
        **Validates: Requirements 10.5**
        """
        product = None
        users = []
        
        try:
            # Create test product with enough inventory
            initial_inventory = 100
            product = self._create_test_product(f"SIMPLE{secrets.randbelow(1000)}", initial_inventory)
            assume(product is not None)
            
            # Create users
            for i in range(thread_count):
                user = self._create_test_user(f"simple{i}{secrets.randbelow(1000)}")
                assume(user is not None)
                users.append(user)
            
            # Track results
            results = []
            errors = []
            
            def add_to_cart_worker(user_id, thread_id):
                """Add items to cart for a specific user."""
                try:
                    # Create new session for this thread
                    thread_db = get_db_session()
                    thread_cart_service = DBCartService(thread_db)
                    
                    result = thread_cart_service.add_cart_item(
                        user_id=user_id,
                        cookie=None,
                        product_id=product.id,
                        size="M",
                        quantity=quantity
                    )
                    
                    thread_db.close()
                    
                    return {
                        'thread_id': thread_id,
                        'user_id': user_id,
                        'success': result is not None,
                        'quantity': quantity if result else 0
                    }
                    
                except Exception as e:
                    return {
                        'thread_id': thread_id,
                        'user_id': user_id,
                        'success': False,
                        'error': str(e)
                    }
            
            # Run concurrent operations
            threads = []
            for i, user in enumerate(users):
                thread = threading.Thread(target=lambda u=user.id, t=i: results.append(add_to_cart_worker(u, t)))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Verify results
            successful_operations = [r for r in results if r.get('success', False)]
            
            # Check inventory consistency
            final_inventory = self.product_service.get_product_inventory(product.id, "M")
            
            # Calculate expected inventory reduction
            total_quantity_added = sum(r['quantity'] for r in successful_operations)
            expected_final_inventory = initial_inventory - total_quantity_added
            
            # Property assertions
            assert final_inventory >= 0, "Inventory should never go negative"
            assert final_inventory == expected_final_inventory, \
                f"Final inventory ({final_inventory}) should match expected ({expected_final_inventory})"
            
            # Verify cart isolation
            for user in users:
                user_cart = self.cart_service.get_cart_contents(user_id=user.id, cookie=None)
                
                # Each user should have their own cart items
                for item in user_cart:
                    assert item.user_id == user.id, f"Cart item should belong to user {user.id}"
                    assert item.cookie is None, "Authenticated user cart items should not have cookies"
            
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
    
    @given(
        operations_count=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_concurrent_inventory_updates_simple(self, operations_count):
        """
        Property: For any simultaneous inventory operations, the final 
        inventory should be mathematically consistent.
        
        **Validates: Requirements 10.5**
        """
        product = None
        
        try:
            # Create test product
            initial_inventory = 50
            product = self._create_test_product(f"INV{secrets.randbelow(1000)}", initial_inventory)
            assume(product is not None)
            
            # Track results
            results = []
            
            def inventory_operation_worker(operation_id):
                """Perform inventory operation."""
                try:
                    # Create new session for this thread
                    thread_db = get_db_session()
                    thread_product_service = ProductService(thread_db)
                    
                    # Try to update inventory (reduce by 1)
                    success = thread_product_service.update_product_inventory(
                        product_id=product.id,
                        size="M",
                        quantity_change=-1
                    )
                    
                    thread_db.close()
                    
                    return {
                        'operation_id': operation_id,
                        'success': success,
                        'change': -1 if success else 0
                    }
                    
                except Exception as e:
                    return {
                        'operation_id': operation_id,
                        'success': False,
                        'error': str(e),
                        'change': 0
                    }
            
            # Run concurrent operations
            threads = []
            for i in range(operations_count):
                thread = threading.Thread(target=lambda op=i: results.append(inventory_operation_worker(op)))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Verify results
            successful_operations = [r for r in results if r.get('success', False)]
            total_change = sum(r['change'] for r in successful_operations)
            
            # Check final inventory
            final_inventory = self.product_service.get_product_inventory(product.id, "M")
            expected_final_inventory = initial_inventory + total_change
            
            # Property assertions
            assert final_inventory >= 0, "Inventory should never go negative"
            assert final_inventory == expected_final_inventory, \
                f"Final inventory ({final_inventory}) should match expected ({expected_final_inventory})"
            
            # Verify no inventory was lost or created unexpectedly
            assert len(successful_operations) <= operations_count, \
                "Number of successful operations should not exceed total operations"
            
        finally:
            # Clean up
            if product:
                try:
                    self.product_service.delete_product(product.id)
                except:
                    pass
    
    @given(
        view_count=st.integers(min_value=2, max_value=4)
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_concurrent_view_increments_simple(self, view_count):
        """
        Property: For any simultaneous view increment operations, the final 
        view count should be consistent with the number of successful operations.
        
        **Validates: Requirements 10.5**
        """
        product = None
        
        try:
            # Create test product
            product = self._create_test_product(f"VIEW{secrets.randbelow(1000)}")
            assume(product is not None)
            
            initial_views = product.product_views
            
            # Track results
            results = []
            
            def view_increment_worker(operation_id):
                """Increment product views."""
                try:
                    # Create new session for this thread
                    thread_db = get_db_session()
                    thread_product_service = ProductService(thread_db)
                    
                    success = thread_product_service.increment_product_views(product.id)
                    
                    thread_db.close()
                    
                    return {
                        'operation_id': operation_id,
                        'success': success
                    }
                    
                except Exception as e:
                    return {
                        'operation_id': operation_id,
                        'success': False,
                        'error': str(e)
                    }
            
            # Run concurrent operations
            threads = []
            for i in range(view_count):
                thread = threading.Thread(target=lambda op=i: results.append(view_increment_worker(op)))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Verify results
            successful_operations = [r for r in results if r.get('success', False)]
            
            # Check final view count
            updated_product = self.product_service.get_product_by_id(product.id)
            final_views = updated_product.product_views
            expected_final_views = initial_views + len(successful_operations)
            
            # Property assertions
            assert final_views >= initial_views, "View count should never decrease"
            assert final_views == expected_final_views, \
                f"Final view count ({final_views}) should match expected ({expected_final_views})"
            
        finally:
            # Clean up
            if product:
                try:
                    self.product_service.delete_product(product.id)
                except:
                    pass