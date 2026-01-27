"""
Property-based tests for input validation and error responses.

**Feature: spoxpro-backend, Property 12: Input Validation and Error Responses**
**Validates: Requirements 7.2, 7.4, 10.1, 10.3, 10.6**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from pydantic import ValidationError
from typing import Dict, Any, List
import json

from backend.DTO import (
    UserRegistrationRequest,
    UserLoginRequest,
    ProductFilterRequest,
    AddToCartRequest,
    CreateOrderRequest,
    CreateProductRequest,
    UpdateProductRequest
)


# Strategy for generating invalid email addresses
@st.composite
def invalid_email_strategy(draw):
    """Generate invalid email addresses."""
    invalid_emails = [
        draw(st.text(min_size=1, max_size=50)),  # Random text
        draw(st.text(min_size=1, max_size=20)) + "@",  # Missing domain
        "@" + draw(st.text(min_size=1, max_size=20)),  # Missing local part
        draw(st.text(min_size=1, max_size=10)) + "@" + draw(st.text(min_size=1, max_size=10)),  # Missing TLD
        "",  # Empty string
        "user@",  # Incomplete
        "@domain.com",  # Missing user
        "user..name@domain.com",  # Double dots
        "user@domain",  # Missing TLD
    ]
    return draw(st.sampled_from(invalid_emails))


# Strategy for generating invalid passwords
@st.composite
def invalid_password_strategy(draw):
    """Generate invalid passwords."""
    invalid_passwords = [
        draw(st.text(max_size=7)),  # Too short
        draw(st.text(min_size=8, alphabet=st.characters(whitelist_categories=("Lu", "Ll")))),  # Only letters
        draw(st.text(min_size=8, alphabet=st.characters(whitelist_categories=("Nd",)))),  # Only numbers
        "",  # Empty
        "1234567",  # Too short with numbers
        "abcdefgh",  # Only letters, no numbers
        "12345678",  # Only numbers, no letters
    ]
    return draw(st.sampled_from(invalid_passwords))


# Strategy for generating invalid phone numbers
@st.composite
def invalid_phone_strategy(draw):
    """Generate invalid phone numbers."""
    invalid_phones = [
        draw(st.text(max_size=9, alphabet=st.characters(whitelist_categories=("Nd",)))),  # Too short
        draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll")))),  # Only letters
        "",  # Empty
        "123",  # Too short
        "abcdefghij",  # Letters only
        "12-34-56",  # Too short with formatting
    ]
    return draw(st.sampled_from(invalid_phones))


class TestInputValidationProperties:
    """Property-based tests for input validation and error responses."""

    @given(
        email=invalid_email_strategy(),
        password=st.text(min_size=8, max_size=128),
        phone=st.text(min_size=10, max_size=20)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_user_registration_invalid_email_property(self, email, password, phone):
        """
        Property 12: Input Validation and Error Responses
        For any invalid email format, the system should validate input using Pydantic models,
        reject invalid requests, and return structured error responses.
        
        **Validates: Requirements 7.2, 7.4, 10.1, 10.3, 10.6**
        """
        # Ensure password has at least one letter and one number for this test
        if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
            password = "validpass123"
        
        # Ensure phone has at least 10 digits for this test
        phone_digits = ''.join(c for c in phone if c.isdigit())
        if len(phone_digits) < 10:
            phone = "+1234567890"
        
        try:
            # Attempt to create registration request with invalid email
            request = UserRegistrationRequest(
                email=email,
                password=password,
                phone=phone
            )
            
            # If validation passes, the email should actually be valid
            # This means our invalid email generator produced a valid email by chance
            assert "@" in email and "." in email.split("@")[-1], \
                f"Email {email} passed validation but appears invalid"
            
        except ValidationError as e:
            # Property: Validation should fail for invalid emails
            assert len(e.errors()) > 0, "ValidationError should contain error details"
            
            # Property: Error should be structured and contain field information
            error_fields = [error["loc"][0] for error in e.errors() if error["loc"]]
            assert "email" in error_fields, "Email validation error should be present"
            
            # Property: Error messages should be descriptive
            for error in e.errors():
                assert "msg" in error, "Error should contain message"
                assert isinstance(error["msg"], str), "Error message should be string"
                assert len(error["msg"]) > 0, "Error message should not be empty"

    @given(
        email=st.emails(),
        password=invalid_password_strategy(),
        phone=st.text(min_size=10, max_size=20)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_user_registration_invalid_password_property(self, email, password, phone):
        """
        Property: Invalid passwords should be rejected with structured error responses.
        
        **Validates: Requirements 7.2, 7.4, 10.1, 10.3, 10.6**
        """
        # Ensure phone has at least 10 digits for this test
        phone_digits = ''.join(c for c in phone if c.isdigit())
        if len(phone_digits) < 10:
            phone = "+1234567890"
        
        try:
            # Attempt to create registration request with invalid password
            request = UserRegistrationRequest(
                email=email,
                password=password,
                phone=phone
            )
            
            # If validation passes, the password should actually be valid
            assert len(password) >= 8, f"Password {password} passed validation but is too short"
            assert any(c.isalpha() for c in password), f"Password {password} passed validation but has no letters"
            assert any(c.isdigit() for c in password), f"Password {password} passed validation but has no numbers"
            
        except ValidationError as e:
            # Property: Validation should fail for invalid passwords
            assert len(e.errors()) > 0, "ValidationError should contain error details"
            
            # Property: Error should be structured and contain field information
            error_fields = [error["loc"][0] for error in e.errors() if error["loc"]]
            assert "password" in error_fields, "Password validation error should be present"

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=128),
        phone=invalid_phone_strategy()
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_user_registration_invalid_phone_property(self, email, password, phone):
        """
        Property: Invalid phone numbers should be rejected with structured error responses.
        
        **Validates: Requirements 7.2, 7.4, 10.1, 10.3, 10.6**
        """
        # Ensure password has at least one letter and one number for this test
        if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
            password = "validpass123"
        
        try:
            # Attempt to create registration request with invalid phone
            request = UserRegistrationRequest(
                email=email,
                password=password,
                phone=phone
            )
            
            # If validation passes, the phone should actually be valid
            phone_digits = ''.join(c for c in phone if c.isdigit())
            assert len(phone_digits) >= 10, f"Phone {phone} passed validation but has insufficient digits"
            
        except ValidationError as e:
            # Property: Validation should fail for invalid phones
            assert len(e.errors()) > 0, "ValidationError should contain error details"
            
            # Property: Error should be structured and contain field information
            error_fields = [error["loc"][0] for error in e.errors() if error["loc"]]
            assert "phone" in error_fields, "Phone validation error should be present"

    @given(
        product_id=st.integers(max_value=0),  # Invalid product IDs (non-positive)
        size=st.sampled_from(["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "XXXXL"]),
        quantity=st.integers(min_value=1, max_value=99)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_add_to_cart_invalid_product_id_property(self, product_id, size, quantity):
        """
        Property: Invalid product IDs should be rejected with structured error responses.
        
        **Validates: Requirements 7.2, 7.4, 10.1, 10.3, 10.6**
        """
        try:
            # Attempt to create cart request with invalid product ID
            request = AddToCartRequest(
                product_id=product_id,
                size=size,
                quantity=quantity
            )
            
            # If validation passes, the product_id should actually be valid
            assert product_id > 0, f"Product ID {product_id} passed validation but is not positive"
            
        except ValidationError as e:
            # Property: Validation should fail for invalid product IDs
            assert len(e.errors()) > 0, "ValidationError should contain error details"
            
            # Property: Error should be structured and contain field information
            error_fields = [error["loc"][0] for error in e.errors() if error["loc"]]
            assert "product_id" in error_fields, "Product ID validation error should be present"

    @given(
        product_id=st.integers(min_value=1, max_value=1000),
        size=st.text(min_size=1, max_size=10),  # Random text instead of valid sizes
        quantity=st.integers(min_value=1, max_value=99)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_add_to_cart_invalid_size_property(self, product_id, size, quantity):
        """
        Property: Invalid sizes should be rejected with structured error responses.
        
        **Validates: Requirements 7.2, 7.4, 10.1, 10.3, 10.6**
        """
        valid_sizes = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "XXXXL"]
        
        # Skip if size happens to be valid
        assume(size not in valid_sizes)
        
        try:
            # Attempt to create cart request with invalid size
            request = AddToCartRequest(
                product_id=product_id,
                size=size,
                quantity=quantity
            )
            
            # If validation passes, this should not happen for invalid sizes
            assert False, f"Size {size} should not pass validation"
            
        except ValidationError as e:
            # Property: Validation should fail for invalid sizes
            assert len(e.errors()) > 0, "ValidationError should contain error details"
            
            # Property: Error should be structured and contain field information
            error_fields = [error["loc"][0] for error in e.errors() if error["loc"]]
            assert "size" in error_fields, "Size validation error should be present"

    @given(
        min_price=st.decimals(min_value=0, max_value=1000, places=2),
        max_price=st.decimals(min_value=0, max_value=1000, places=2)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_product_filter_invalid_price_range_property(self, min_price, max_price):
        """
        Property: Invalid price ranges (max < min) should be rejected with structured error responses.
        
        **Validates: Requirements 7.2, 7.4, 10.1, 10.3, 10.6**
        """
        # Only test cases where max_price < min_price
        assume(max_price < min_price)
        
        try:
            # Attempt to create filter request with invalid price range
            request = ProductFilterRequest(
                min_price=min_price,
                max_price=max_price
            )
            
            # If validation passes, this should not happen for invalid ranges
            assert False, f"Price range min={min_price}, max={max_price} should not pass validation"
            
        except ValidationError as e:
            # Property: Validation should fail for invalid price ranges
            assert len(e.errors()) > 0, "ValidationError should contain error details"
            
            # Property: Error should be structured and contain field information
            error_fields = [error["loc"][0] for error in e.errors() if error["loc"]]
            assert "max_price" in error_fields, "Price range validation error should be present"

    @given(
        sort_by=st.text(min_size=1, max_size=20),
        sort_order=st.text(min_size=1, max_size=10)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_product_filter_invalid_sort_parameters_property(self, sort_by, sort_order):
        """
        Property: Invalid sort parameters should be rejected with structured error responses.
        
        **Validates: Requirements 7.2, 7.4, 10.1, 10.3, 10.6**
        """
        valid_sort_by = ["name", "price", "created_date", "product_views", "brand"]
        valid_sort_order = ["asc", "desc"]
        
        # Skip if parameters happen to be valid
        assume(sort_by not in valid_sort_by or sort_order not in valid_sort_order)
        
        try:
            # Attempt to create filter request with invalid sort parameters
            request = ProductFilterRequest(
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            # If validation passes, parameters should actually be valid
            if sort_by not in valid_sort_by:
                assert False, f"Sort by {sort_by} should not pass validation"
            if sort_order not in valid_sort_order:
                assert False, f"Sort order {sort_order} should not pass validation"
            
        except ValidationError as e:
            # Property: Validation should fail for invalid sort parameters
            assert len(e.errors()) > 0, "ValidationError should contain error details"
            
            # Property: Error should be structured and contain field information
            error_fields = [error["loc"][0] for error in e.errors() if error["loc"]]
            invalid_fields = []
            if sort_by not in valid_sort_by:
                invalid_fields.append("sort_by")
            if sort_order not in valid_sort_order:
                invalid_fields.append("sort_order")
            
            # At least one invalid field should be in the error
            assert any(field in error_fields for field in invalid_fields), \
                f"Expected validation errors for fields {invalid_fields}, got errors for {error_fields}"

    @given(
        shipping_address=st.text(max_size=9),  # Too short
        payment_method=st.text(min_size=1, max_size=20)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_create_order_invalid_data_property(self, shipping_address, payment_method):
        """
        Property: Invalid order data should be rejected with structured error responses.
        
        **Validates: Requirements 7.2, 7.4, 10.1, 10.3, 10.6**
        """
        valid_payment_methods = ["credit_card", "debit_card", "paypal", "bank_transfer", "cash_on_delivery"]
        
        # Skip if payment method happens to be valid and address is long enough
        assume(len(shipping_address) < 10 or payment_method not in valid_payment_methods)
        
        try:
            # Attempt to create order request with invalid data
            request = CreateOrderRequest(
                shipping_address=shipping_address,
                payment_method=payment_method
            )
            
            # If validation passes, data should actually be valid
            if len(shipping_address) < 10:
                assert False, f"Shipping address '{shipping_address}' should not pass validation (too short)"
            if payment_method not in valid_payment_methods:
                assert False, f"Payment method '{payment_method}' should not pass validation"
            
        except ValidationError as e:
            # Property: Validation should fail for invalid data
            assert len(e.errors()) > 0, "ValidationError should contain error details"
            
            # Property: Error should be structured and contain field information
            error_fields = [error["loc"][0] for error in e.errors() if error["loc"]]
            
            # Check which fields should have errors
            expected_errors = []
            if len(shipping_address) < 10:
                expected_errors.append("shipping_address")
            if payment_method not in valid_payment_methods:
                expected_errors.append("payment_method")
            
            # At least one expected error should be present
            assert any(field in error_fields for field in expected_errors), \
                f"Expected validation errors for fields {expected_errors}, got errors for {error_fields}"

    @given(data=st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.floats(), st.booleans())))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_validation_error_structure_consistency_property(self, data):
        """
        Property: All validation errors should have consistent structure across different models.
        
        **Validates: Requirements 7.2, 7.4, 10.1, 10.3, 10.6**
        """
        models_to_test = [
            UserRegistrationRequest,
            UserLoginRequest,
            AddToCartRequest,
            CreateOrderRequest
        ]
        
        for model_class in models_to_test:
            try:
                # Attempt to create model with random data
                model_class(**data)
                
            except ValidationError as e:
                # Property: All validation errors should have consistent structure
                assert isinstance(e.errors(), list), "Errors should be a list"
                assert len(e.errors()) > 0, "Error list should not be empty"
                
                for error in e.errors():
                    # Property: Each error should have required fields
                    assert isinstance(error, dict), "Each error should be a dictionary"
                    assert "loc" in error, "Error should have 'loc' field"
                    assert "msg" in error, "Error should have 'msg' field"
                    assert "type" in error, "Error should have 'type' field"
                    
                    # Property: Error fields should have correct types
                    assert isinstance(error["loc"], (list, tuple)), "Error location should be list or tuple"
                    assert isinstance(error["msg"], str), "Error message should be string"
                    assert isinstance(error["type"], str), "Error type should be string"
                    
                    # Property: Error message should not be empty
                    assert len(error["msg"]) > 0, "Error message should not be empty"
                    
            except Exception as e:
                # Other exceptions are acceptable (e.g., TypeError for completely wrong data types)
                pass
