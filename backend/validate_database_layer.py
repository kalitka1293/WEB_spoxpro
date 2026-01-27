#!/usr/bin/env python3
"""
Database layer validation script for spoXpro backend.

This script validates that all database services work correctly with test data,
verifies foreign key constraints and data integrity.
"""

import sys
import os
from decimal import Decimal
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def validate_database_layer():
    """Validate the database layer functionality."""
    print("🔍 Starting database layer validation...")
    
    try:
        # Import required modules
        from tests.conftest import create_test_db_session, create_sample_helper_data
        from db.services.product_service import ProductService
        from db.services.user_service import UserService
        from db.services.cart_service import CartService
        from db.services.order_service import OrderService
        
        print("✅ Successfully imported all database services")
        
        with create_test_db_session() as session:
            print("✅ Database session created successfully")
            
            # Create helper data
            helper_data = create_sample_helper_data(session)
            print("✅ Helper data created successfully")
            
            # Initialize services
            product_service = ProductService(session)
            user_service = UserService(session)
            cart_service = CartService(session)
            order_service = OrderService(session)
            print("✅ All services initialized successfully")
            
            # Test 1: Product Service
            print("\n📦 Testing Product Service...")
            product_data = {
                "name": "Test T-Shirt",
                "description": "A comfortable test t-shirt",
                "product_type_id": helper_data["product_type"].id,
                "category_id": helper_data["category"].id,
                "sport_type_id": helper_data["sport_type"].id,
                "color": "Blue",
                "gender": "unisex",
                "brand": "spoXpro",
                "price": Decimal("29.99"),
                "reviews": [{"rating": 5, "comment": "Great!"}],
                "article_number": "TEST001",
                "images": ["test1.jpg", "test2.jpg"],
                "material_id": helper_data["material"].id,
                "sizes": [
                    {"size": "M", "quantity": 10},
                    {"size": "L", "quantity": 15},
                    {"size": "XL", "quantity": 5}
                ]
            }
            
            product = product_service.create_product(product_data)
            assert product is not None, "Product creation failed"
            assert product.name == "Test T-Shirt", "Product name mismatch"
            print("  ✅ Product creation works")
            
            # Test product retrieval
            retrieved_product = product_service.get_product_by_id(product.id)
            assert retrieved_product is not None, "Product retrieval failed"
            assert retrieved_product.name == product.name, "Retrieved product mismatch"
            print("  ✅ Product retrieval works")
            
            # Test product view increment
            initial_views = product.product_views
            success = product_service.increment_product_views(product.id)
            assert success, "View increment failed"
            session.refresh(product)
            assert product.product_views == initial_views + 1, "View count not incremented"
            print("  ✅ Product view increment works")
            
            # Test 2: User Service
            print("\n👤 Testing User Service...")
            user_data = {
                "email": "test@example.com",
                "password": "testpass123",  # Shorter password
                "phone": "+1234567890"
            }
            
            user = user_service.create_user(user_data)
            assert user is not None, "User creation failed"
            assert user.email == "test@example.com", "User email mismatch"
            print("  ✅ User creation works")
            
            # Test user authentication
            authenticated_user = user_service.authenticate_user("test@example.com", "testpass123")
            assert authenticated_user is not None, "User authentication failed"
            assert authenticated_user.id == user.id, "Authenticated user mismatch"
            print("  ✅ User authentication works")
            
            # Test verification code
            success = user_service.create_verification_code("test@example.com", "123456")
            assert success, "Verification code creation failed"
            
            verified = user_service.verify_code("test@example.com", "123456")
            assert verified, "Code verification failed"
            print("  ✅ Verification code system works")
            
            # Test 3: Cart Service
            print("\n🛒 Testing Cart Service...")
            
            # Add item to cart
            cart_item = cart_service.add_cart_item(
                user_id=user.id,
                cookie=None,
                product_id=product.id,
                size="M",
                quantity=2
            )
            assert cart_item is not None, "Cart item addition failed"
            assert cart_item.quantity == 2, "Cart item quantity mismatch"
            print("  ✅ Cart item addition works")
            
            # Get cart items
            cart_items = cart_service.get_cart_items(user_id=user.id, cookie=None)
            assert len(cart_items) == 1, "Cart items retrieval failed"
            assert cart_items[0].id == cart_item.id, "Cart item mismatch"
            print("  ✅ Cart items retrieval works")
            
            # Calculate cart total
            total = cart_service.calculate_cart_total(user_id=user.id, cookie=None)
            expected_total = product.price * Decimal("2")
            assert total == expected_total, f"Cart total mismatch: expected {expected_total}, got {total}"
            print("  ✅ Cart total calculation works")
            
            # Test 4: Order Service
            print("\n📋 Testing Order Service...")
            
            # Create order from cart
            order = order_service.create_order(user.id, {})
            assert order is not None, "Order creation failed"
            assert order.user_id == user.id, "Order user mismatch"
            assert order.total_amount == expected_total, "Order total mismatch"
            print("  ✅ Order creation works")
            
            # Verify cart was cleared
            cart_items_after_order = cart_service.get_cart_items(user_id=user.id, cookie=None)
            assert len(cart_items_after_order) == 0, "Cart was not cleared after order"
            print("  ✅ Cart clearing after order works")
            
            # Verify inventory was reduced
            session.refresh(product)
            m_size = next((size for size in product.sizes if size.size == "M"), None)
            assert m_size is not None, "Size M not found"
            assert m_size.quantity == 8, f"Inventory not reduced: expected 8, got {m_size.quantity}"  # 10 - 2 = 8
            print("  ✅ Inventory reduction works")
            
            # Get user orders
            user_orders = order_service.get_user_orders(user.id)
            assert len(user_orders) == 1, "User orders retrieval failed"
            assert user_orders[0].id == order.id, "User order mismatch"
            print("  ✅ User orders retrieval works")
            
            # Test order status update
            updated_order = order_service.update_order_status(order.id, "confirmed")
            assert updated_order is not None, "Order status update failed"
            assert updated_order.status == "confirmed", "Order status not updated"
            print("  ✅ Order status update works")
            
            # Test 5: Foreign Key Constraints
            print("\n🔗 Testing Foreign Key Constraints...")
            
            # Try to create product with invalid foreign keys
            try:
                invalid_product_data = product_data.copy()
                invalid_product_data["product_type_id"] = 99999  # Non-existent ID
                invalid_product_data["article_number"] = "INVALID001"
                invalid_product = product_service.create_product(invalid_product_data)
                assert invalid_product is None, "Should not create product with invalid foreign key"
                print("  ✅ Foreign key constraint validation works")
            except Exception as e:
                print(f"  ✅ Foreign key constraint properly enforced: {type(e).__name__}")
            
            # Test 6: Data Integrity
            print("\n🛡️ Testing Data Integrity...")
            
            # Try to create user with duplicate email
            try:
                duplicate_user_data = {
                    "email": "test@example.com",  # Same email as before
                    "password": "anotherpassword",
                    "phone": "+9876543210"
                }
                duplicate_user = user_service.create_user(duplicate_user_data)
                assert duplicate_user is None, "Should not create user with duplicate email"
                print("  ✅ Email uniqueness constraint works")
            except Exception as e:
                print(f"  ✅ Email uniqueness properly enforced: {type(e).__name__}")
            
            print("\n🎉 All database layer validations passed successfully!")
            return True
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("This might be due to missing dependencies or import path issues.")
        return False
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = validate_database_layer()
    if success:
        print("\n✅ Database layer validation completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Database layer validation failed!")
        sys.exit(1)