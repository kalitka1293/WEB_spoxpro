"""
Property-based tests for database referential integrity.

**Feature: spoxpro-backend, Property 4: Database Referential Integrity**
**Validates: Requirements 1.6, 6.3**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import uuid

from backend.db.models.product import Product, ProductSize, ProductType, Category, SportType, Material
from backend.db.models.user import User, VerificationCode
from backend.db.models.order import CartItem, Order, OrderItem
from .conftest import create_test_db_session, create_sample_helper_data


# Valid data constants
VALID_SIZES = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "XXXXL"]
VALID_GENDERS = ["male", "female", "unisex"]
VALID_ORDER_STATUSES = ["pending", "confirmed", "shipped", "delivered", "cancelled"]


# Hypothesis strategies for generating test data
@st.composite
def valid_user_data_strategy(draw):
    """Generate valid user data for testing."""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"user_{unique_id}@example.com",
        "password_hash": draw(st.text(min_size=10, max_size=255)),
        "phone": draw(st.text(min_size=10, max_size=20, alphabet="0123456789")),
        "cookie": draw(st.one_of(st.none(), st.text(min_size=10, max_size=255)))
    }


@st.composite
def valid_product_data_strategy(draw):
    """Generate valid product data for testing."""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "name": draw(st.text(min_size=1, max_size=200)),
        "description": draw(st.text(min_size=1, max_size=1000)),
        "color": draw(st.text(min_size=1, max_size=50)),
        "gender": draw(st.sampled_from(VALID_GENDERS)),
        "brand": "spoXpro",
        "price": draw(st.decimals(min_value=Decimal("0.01"), max_value=Decimal("9999.99"), places=2)),
        "article_number": f"ART_{unique_id}",
        "reviews": [],
        "images": []
    }


@st.composite
def invalid_foreign_key_strategy(draw):
    """Generate invalid foreign key IDs that don't exist in the database."""
    return draw(st.integers(min_value=99999, max_value=999999))


class TestReferentialIntegrityProperties:
    """Property-based tests for database referential integrity constraints."""

    @given(valid_product_data_strategy(), invalid_foreign_key_strategy())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_product_with_invalid_foreign_keys_rejected(self, product_data, invalid_fk):
        """
        Property: For any product data with invalid foreign key references,
        the database should reject the operation and raise IntegrityError.
        
        **Validates: Requirements 1.6, 6.3**
        """
        session = create_test_db_session()
        try:
            # Create helper data first
            create_sample_helper_data(session)
            
            # Test invalid product_type_id
            product_data_copy = product_data.copy()
            product_data_copy["product_type_id"] = invalid_fk
            
            product = Product(**product_data_copy)
            session.add(product)
            
            with pytest.raises(IntegrityError):
                session.commit()
            
            session.rollback()
            
            # Test invalid category_id
            product_data_copy = product_data.copy()
            product_data_copy["category_id"] = invalid_fk
            
            product = Product(**product_data_copy)
            session.add(product)
            
            with pytest.raises(IntegrityError):
                session.commit()
            
            session.rollback()
            
            # Test invalid sport_type_id
            product_data_copy = product_data.copy()
            product_data_copy["sport_type_id"] = invalid_fk
            
            product = Product(**product_data_copy)
            session.add(product)
            
            with pytest.raises(IntegrityError):
                session.commit()
            
            session.rollback()
            
            # Test invalid material_id
            product_data_copy = product_data.copy()
            product_data_copy["material_id"] = invalid_fk
            
            product = Product(**product_data_copy)
            session.add(product)
            
            with pytest.raises(IntegrityError):
                session.commit()
                
        finally:
            session.close()

    @given(st.sampled_from(VALID_SIZES), st.integers(min_value=0, max_value=1000), invalid_foreign_key_strategy())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_product_size_with_invalid_product_id_rejected(self, size, quantity, invalid_product_id):
        """
        Property: For any ProductSize with invalid product_id foreign key,
        the database should reject the operation and raise IntegrityError.
        
        **Validates: Requirements 1.6, 6.3**
        """
        session = create_test_db_session()
        try:
            product_size = ProductSize(
                product_id=invalid_product_id,
                size=size,
                quantity=quantity
            )
            session.add(product_size)
            
            with pytest.raises(IntegrityError):
                session.commit()
                
        finally:
            session.close()

    @given(valid_user_data_strategy(), invalid_foreign_key_strategy(), 
           st.sampled_from(VALID_SIZES), st.integers(min_value=1, max_value=10))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_cart_item_with_invalid_foreign_keys_rejected(self, user_data, invalid_fk, size, quantity):
        """
        Property: For any CartItem with invalid foreign key references,
        the database should reject the operation and raise IntegrityError.
        
        **Validates: Requirements 1.6, 6.3**
        """
        session = create_test_db_session()
        try:
            # Create a valid user first
            user = User(**user_data)
            session.add(user)
            session.commit()
            
            # Test invalid product_id
            cart_item = CartItem(
                user_id=user.id,
                product_id=invalid_fk,
                size=size,
                quantity=quantity
            )
            session.add(cart_item)
            
            with pytest.raises(IntegrityError):
                session.commit()
            
            session.rollback()
            
            # Test invalid user_id (when not using cookie)
            cart_item = CartItem(
                user_id=invalid_fk,
                product_id=1,  # This will also be invalid, but user_id constraint hits first
                size=size,
                quantity=quantity
            )
            session.add(cart_item)
            
            with pytest.raises(IntegrityError):
                session.commit()
                
        finally:
            session.close()

    @given(valid_user_data_strategy(), invalid_foreign_key_strategy())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_order_with_invalid_user_id_rejected(self, user_data, invalid_user_id):
        """
        Property: For any Order with invalid user_id foreign key,
        the database should reject the operation and raise IntegrityError.
        
        **Validates: Requirements 1.6, 6.3**
        """
        session = create_test_db_session()
        try:
            order = Order(
                user_id=invalid_user_id,
                total_amount=Decimal("99.99"),
                status="pending"
            )
            session.add(order)
            
            with pytest.raises(IntegrityError):
                session.commit()
                
        finally:
            session.close()

    @given(invalid_foreign_key_strategy(), invalid_foreign_key_strategy(), 
           st.sampled_from(VALID_SIZES), st.integers(min_value=1, max_value=10))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_order_item_with_invalid_foreign_keys_rejected(self, invalid_order_id, invalid_product_id, size, quantity):
        """
        Property: For any OrderItem with invalid foreign key references,
        the database should reject the operation and raise IntegrityError.
        
        **Validates: Requirements 1.6, 6.3**
        """
        session = create_test_db_session()
        try:
            order_item = OrderItem(
                order_id=invalid_order_id,
                product_id=invalid_product_id,
                size=size,
                quantity=quantity,
                price_at_time=Decimal("29.99")
            )
            session.add(order_item)
            
            with pytest.raises(IntegrityError):
                session.commit()
                
        finally:
            session.close()

    @given(st.text(min_size=1, max_size=255), st.text(min_size=1, max_size=10))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_verification_code_referential_integrity(self, email, code):
        """
        Property: VerificationCode should maintain referential integrity
        and allow creation without foreign key constraints.
        
        **Validates: Requirements 1.6, 6.3**
        """
        session = create_test_db_session()
        try:
            verification = VerificationCode(
                email=email,
                code=code,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            session.add(verification)
            session.commit()
            
            # Should succeed as VerificationCode doesn't have foreign key constraints
            assert verification.id is not None
            assert verification.email == email
            assert verification.code == code
            
        finally:
            session.close()

    @given(valid_product_data_strategy())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_product_with_valid_foreign_keys_accepted(self, product_data):
        """
        Property: For any product data with valid foreign key references,
        the database should accept the operation successfully.
        
        **Validates: Requirements 1.6, 6.3**
        """
        session = create_test_db_session()
        try:
            # Create helper data first
            helper_data = create_sample_helper_data(session)
            
            # Use valid foreign keys from helper data
            product_data["product_type_id"] = helper_data["product_type"].id
            product_data["category_id"] = helper_data["category"].id
            product_data["sport_type_id"] = helper_data["sport_type"].id
            product_data["material_id"] = helper_data["material"].id
            
            product = Product(**product_data)
            session.add(product)
            session.commit()
            
            # Should succeed with valid foreign keys
            assert product.id is not None
            assert product.product_type_id == helper_data["product_type"].id
            assert product.category_id == helper_data["category"].id
            assert product.sport_type_id == helper_data["sport_type"].id
            assert product.material_id == helper_data["material"].id
            
        finally:
            session.close()

    @given(valid_user_data_strategy(), st.sampled_from(VALID_SIZES), st.integers(min_value=1, max_value=10))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_cart_item_with_valid_foreign_keys_accepted(self, user_data, size, quantity):
        """
        Property: For any CartItem with valid foreign key references,
        the database should accept the operation successfully.
        
        **Validates: Requirements 1.6, 6.3**
        """
        session = create_test_db_session()
        try:
            # Create helper data and valid user/product
            helper_data = create_sample_helper_data(session)
            
            user = User(**user_data)
            session.add(user)
            session.commit()
            
            product_data = {
                "name": "Test Product",
                "description": "Test Description",
                "product_type_id": helper_data["product_type"].id,
                "category_id": helper_data["category"].id,
                "sport_type_id": helper_data["sport_type"].id,
                "color": "Blue",
                "gender": "unisex",
                "brand": "spoXpro",
                "price": Decimal("29.99"),
                "article_number": f"ART_{uuid.uuid4().hex[:8]}",
                "reviews": [],
                "images": [],
                "material_id": helper_data["material"].id
            }
            
            product = Product(**product_data)
            session.add(product)
            session.commit()
            
            # Create cart item with valid foreign keys
            cart_item = CartItem(
                user_id=user.id,
                product_id=product.id,
                size=size,
                quantity=quantity
            )
            session.add(cart_item)
            session.commit()
            
            # Should succeed with valid foreign keys
            assert cart_item.id is not None
            assert cart_item.user_id == user.id
            assert cart_item.product_id == product.id
            
        finally:
            session.close()

    @given(valid_user_data_strategy(), st.sampled_from(VALID_SIZES), st.integers(min_value=1, max_value=10))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_order_and_order_item_with_valid_foreign_keys_accepted(self, user_data, size, quantity):
        """
        Property: For any Order and OrderItem with valid foreign key references,
        the database should accept the operations successfully.
        
        **Validates: Requirements 1.6, 6.3**
        """
        session = create_test_db_session()
        try:
            # Create helper data and valid user/product
            helper_data = create_sample_helper_data(session)
            
            user = User(**user_data)
            session.add(user)
            session.commit()
            
            product_data = {
                "name": "Test Product",
                "description": "Test Description",
                "product_type_id": helper_data["product_type"].id,
                "category_id": helper_data["category"].id,
                "sport_type_id": helper_data["sport_type"].id,
                "color": "Blue",
                "gender": "unisex",
                "brand": "spoXpro",
                "price": Decimal("29.99"),
                "article_number": f"ART_{uuid.uuid4().hex[:8]}",
                "reviews": [],
                "images": [],
                "material_id": helper_data["material"].id
            }
            
            product = Product(**product_data)
            session.add(product)
            session.commit()
            
            # Create order with valid foreign keys
            order = Order(
                user_id=user.id,
                total_amount=Decimal("99.99"),
                status="pending"
            )
            session.add(order)
            session.commit()
            
            # Create order item with valid foreign keys
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                size=size,
                quantity=quantity,
                price_at_time=Decimal("29.99")
            )
            session.add(order_item)
            session.commit()
            
            # Should succeed with valid foreign keys
            assert order.id is not None
            assert order.user_id == user.id
            assert order_item.id is not None
            assert order_item.order_id == order.id
            assert order_item.product_id == product.id
            
        finally:
            session.close()

    @given(st.text(min_size=1, max_size=255), invalid_foreign_key_strategy(), 
           st.sampled_from(VALID_SIZES), st.integers(min_value=1, max_value=10))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_guest_cart_item_with_invalid_product_id_rejected(self, cookie, invalid_product_id, size, quantity):
        """
        Property: For any guest CartItem (using cookie) with invalid product_id foreign key,
        the database should reject the operation and raise IntegrityError.
        
        **Validates: Requirements 1.6, 6.3**
        """
        session = create_test_db_session()
        try:
            # Test guest cart item with invalid product_id
            cart_item = CartItem(
                user_id=None,  # Guest user
                cookie=cookie,
                product_id=invalid_product_id,
                size=size,
                quantity=quantity
            )
            session.add(cart_item)
            
            with pytest.raises(IntegrityError):
                session.commit()
                
        finally:
            session.close()

    @given(st.text(min_size=1, max_size=255), st.sampled_from(VALID_SIZES), st.integers(min_value=1, max_value=10))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_guest_cart_item_with_valid_product_id_accepted(self, cookie, size, quantity):
        """
        Property: For any guest CartItem (using cookie) with valid product_id foreign key,
        the database should accept the operation successfully.
        
        **Validates: Requirements 1.6, 6.3**
        """
        session = create_test_db_session()
        try:
            # Create helper data and valid product
            helper_data = create_sample_helper_data(session)
            
            product_data = {
                "name": "Test Product",
                "description": "Test Description",
                "product_type_id": helper_data["product_type"].id,
                "category_id": helper_data["category"].id,
                "sport_type_id": helper_data["sport_type"].id,
                "color": "Blue",
                "gender": "unisex",
                "brand": "spoXpro",
                "price": Decimal("29.99"),
                "article_number": f"ART_{uuid.uuid4().hex[:8]}",
                "reviews": [],
                "images": [],
                "material_id": helper_data["material"].id
            }
            
            product = Product(**product_data)
            session.add(product)
            session.commit()
            
            # Create guest cart item with valid foreign keys
            cart_item = CartItem(
                user_id=None,  # Guest user
                cookie=cookie,
                product_id=product.id,
                size=size,
                quantity=quantity
            )
            session.add(cart_item)
            session.commit()
            
            # Should succeed with valid foreign keys
            assert cart_item.id is not None
            assert cart_item.user_id is None
            assert cart_item.cookie == cookie
            assert cart_item.product_id == product.id
            
        finally:
            session.close()

    @given(invalid_foreign_key_strategy())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_cascade_delete_behavior_with_foreign_keys(self, invalid_fk):
        """
        Property: For any valid entities with foreign key relationships,
        cascade delete behavior should maintain referential integrity.
        
        **Validates: Requirements 1.6, 6.3**
        """
        session = create_test_db_session()
        try:
            # Create helper data and valid entities
            helper_data = create_sample_helper_data(session)
            
            user_data = {
                "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
                "password_hash": "hashed_password",
                "phone": "1234567890"
            }
            user = User(**user_data)
            session.add(user)
            session.commit()
            
            product_data = {
                "name": "Test Product",
                "description": "Test Description",
                "product_type_id": helper_data["product_type"].id,
                "category_id": helper_data["category"].id,
                "sport_type_id": helper_data["sport_type"].id,
                "color": "Blue",
                "gender": "unisex",
                "brand": "spoXpro",
                "price": Decimal("29.99"),
                "article_number": f"ART_{uuid.uuid4().hex[:8]}",
                "reviews": [],
                "images": [],
                "material_id": helper_data["material"].id
            }
            
            product = Product(**product_data)
            session.add(product)
            session.commit()
            
            # Create product size
            product_size = ProductSize(
                product_id=product.id,
                size="M",
                quantity=10
            )
            session.add(product_size)
            session.commit()
            
            # Create cart item
            cart_item = CartItem(
                user_id=user.id,
                product_id=product.id,
                size="M",
                quantity=2
            )
            session.add(cart_item)
            session.commit()
            
            # Create order and order item
            order = Order(
                user_id=user.id,
                total_amount=Decimal("59.98"),
                status="pending"
            )
            session.add(order)
            session.commit()
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                size="M",
                quantity=2,
                price_at_time=Decimal("29.99")
            )
            session.add(order_item)
            session.commit()
            
            # Verify all entities exist
            assert product_size.id is not None
            assert cart_item.id is not None
            assert order.id is not None
            assert order_item.id is not None
            
            # Delete product - should cascade to product_size but not to cart_item/order_item
            # (they should be protected by foreign key constraints)
            session.delete(product)
            
            # This should raise IntegrityError due to existing cart_item and order_item references
            with pytest.raises(IntegrityError):
                session.commit()
                
        finally:
            session.close()
