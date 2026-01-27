"""
Property-based tests for user authentication functionality.

**Feature: spoxpro-backend, Property 5: User Registration and Authentication**
**Validates: Requirements 2.1, 2.2, 2.6**

These tests verify that for any valid user registration data (email, password, phone),
the system creates a user account with properly hashed password and generates valid
JWT tokens for subsequent authentication.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..service.auth_service import AuthService
from ..db.services.user_service import UserService
from ..db.main import get_db_session
from ..config.database import Base, engine


# Test data strategies
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
    
    # Add optional special characters and more letters/numbers
    extra = draw(st.text(
        alphabet='abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()',
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
    # Generate 10-15 digit phone numbers with optional formatting
    digits = draw(st.text(alphabet='0123456789', min_size=10, max_size=15))
    
    # Optionally add formatting
    format_choice = draw(st.integers(0, 3))
    if format_choice == 0:
        return digits
    elif format_choice == 1:
        return f"+1{digits}"
    elif format_choice == 2 and len(digits) >= 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    else:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}" if len(digits) >= 10 else digits


@st.composite
def invalid_password_strategy(draw):
    """Generate invalid passwords that don't meet requirements."""
    choice = draw(st.integers(0, 3))
    
    if choice == 0:
        # Too short
        return draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', max_size=7))
    elif choice == 1:
        # Too long
        return draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=129, max_size=200))
    elif choice == 2:
        # No numbers
        return draw(st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz',
            min_size=8,
            max_size=20
        ))
    else:
        # No letters
        return draw(st.text(
            alphabet='0123456789!@#$%^&*()',
            min_size=8,
            max_size=20
        ))


class TestUserAuthenticationProperties:
    """Property-based tests for user authentication."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a clean database for each test."""
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Get database session
        self.db = get_db_session()
        self.user_service = UserService(self.db)
        self.auth_service = AuthService(self.user_service)
        
        yield
        
        # Clean up
        self.db.close()
        Base.metadata.drop_all(bind=engine)
    
    @given(
        email=valid_email_strategy(),
        password=valid_password_strategy(),
        phone=valid_phone_strategy()
    )
    @settings(max_examples=20, deadline=5000)
    def test_property_valid_user_registration_creates_account(self, email, password, phone):
        """
        Property: For any valid user registration data, the system should create
        a user account with properly hashed password.
        
        **Validates: Requirements 2.1, 2.6**
        """
        # Assume valid inputs (filter out edge cases that might cause issues)
        assume(len(email) <= 255)
        assume(len(phone) <= 20)
        assume('@' in email and '.' in email)
        
        # Register user
        user = self.auth_service.register_user(email, password, phone)
        
        # Verify user was created
        assert user is not None
        assert user.email == email
        assert user.phone == phone
        assert user.password_hash != password  # Password should be hashed
        assert len(user.password_hash) > 0
        assert user.created_date is not None
        
        # Verify password was hashed correctly (can be verified)
        assert self.user_service.verify_password(password, user.password_hash)
        
        # Verify user can be retrieved
        retrieved_user = self.user_service.get_user_by_email(email)
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
    
    @given(
        email=valid_email_strategy(),
        password=valid_password_strategy(),
        phone=valid_phone_strategy()
    )
    @settings(max_examples=20, deadline=5000)
    def test_property_duplicate_email_registration_fails(self, email, password, phone):
        """
        Property: For any email address, attempting to register twice should fail
        on the second attempt.
        
        **Validates: Requirements 2.1**
        """
        assume(len(email) <= 255)
        assume(len(phone) <= 20)
        assume('@' in email and '.' in email)
        
        # First registration should succeed
        user1 = self.auth_service.register_user(email, password, phone)
        assert user1 is not None
        
        # Second registration with same email should fail
        with pytest.raises(ValueError, match="Email address is already registered"):
            self.auth_service.register_user(email, password + "different", phone)
    
    @given(
        email=valid_email_strategy(),
        invalid_password=invalid_password_strategy(),
        phone=valid_phone_strategy()
    )
    @settings(max_examples=20, deadline=5000)
    def test_property_invalid_password_registration_fails(self, email, invalid_password, phone):
        """
        Property: For any invalid password, user registration should fail with
        appropriate error message.
        
        **Validates: Requirements 2.6**
        """
        assume(len(email) <= 255)
        assume(len(phone) <= 20)
        assume('@' in email and '.' in email)
        
        # Registration with invalid password should fail
        with pytest.raises(ValueError) as exc_info:
            self.auth_service.register_user(email, invalid_password, phone)
        
        # Error message should be descriptive
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in [
            'password', 'character', 'letter', 'number', 'length'
        ])
    
    @given(
        email=valid_email_strategy(),
        password=valid_password_strategy(),
        phone=valid_phone_strategy()
    )
    @settings(max_examples=20, deadline=5000)
    def test_property_valid_authentication_succeeds(self, email, password, phone):
        """
        Property: For any registered user with valid credentials, authentication
        should succeed and return the user object.
        
        **Validates: Requirements 2.2**
        """
        assume(len(email) <= 255)
        assume(len(phone) <= 20)
        assume('@' in email and '.' in email)
        
        # Register user first
        registered_user = self.auth_service.register_user(email, password, phone)
        assert registered_user is not None
        
        # Authentication with correct credentials should succeed
        authenticated_user = self.auth_service.authenticate_user(email, password)
        assert authenticated_user is not None
        assert authenticated_user.id == registered_user.id
        assert authenticated_user.email == email
    
    @given(
        email=valid_email_strategy(),
        password=valid_password_strategy(),
        wrong_password=valid_password_strategy(),
        phone=valid_phone_strategy()
    )
    @settings(max_examples=20, deadline=5000)
    def test_property_invalid_authentication_fails(self, email, password, wrong_password, phone):
        """
        Property: For any registered user, authentication with wrong password
        should fail and return None.
        
        **Validates: Requirements 2.2**
        """
        assume(len(email) <= 255)
        assume(len(phone) <= 20)
        assume('@' in email and '.' in email)
        assume(password != wrong_password)  # Ensure passwords are different
        
        # Register user first
        registered_user = self.auth_service.register_user(email, password, phone)
        assert registered_user is not None
        
        # Authentication with wrong password should fail
        authenticated_user = self.auth_service.authenticate_user(email, wrong_password)
        assert authenticated_user is None
    
    @given(
        email=valid_email_strategy(),
        password=valid_password_strategy(),
        phone=valid_phone_strategy()
    )
    @settings(max_examples=20, deadline=5000)
    def test_property_jwt_token_generation_and_validation(self, email, password, phone):
        """
        Property: For any registered user, JWT token generation should create
        valid tokens that can be validated to extract user information.
        
        **Validates: Requirements 2.2, 2.3**
        """
        assume(len(email) <= 255)
        assume(len(phone) <= 20)
        assume('@' in email and '.' in email)
        
        # Register and authenticate user
        user = self.auth_service.register_user(email, password, phone)
        assert user is not None
        
        # Generate JWT token
        token_data = self.auth_service.generate_jwt_token(user)
        assert token_data is not None
        assert "access_token" in token_data
        assert "token_type" in token_data
        assert "user_id" in token_data
        assert "email" in token_data
        assert "expires_in" in token_data
        
        assert token_data["token_type"] == "bearer"
        assert token_data["user_id"] == user.id
        assert token_data["email"] == user.email
        assert token_data["expires_in"] > 0
        
        # Validate the generated token
        validation_result = self.auth_service.validate_jwt_token(token_data["access_token"])
        assert validation_result is not None
        assert validation_result["user_id"] == user.id
        assert validation_result["email"] == user.email
        assert validation_result["expires_at"] > datetime.utcnow()
    
    @given(
        invalid_token=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=10, deadline=5000)
    def test_property_invalid_jwt_token_validation_fails(self, invalid_token):
        """
        Property: For any invalid JWT token, validation should fail and return None.
        
        **Validates: Requirements 2.3**
        """
        # Assume it's not accidentally a valid token format
        assume(not invalid_token.startswith('eyJ'))  # JWT tokens start with eyJ
        
        # Invalid token validation should fail
        validation_result = self.auth_service.validate_jwt_token(invalid_token)
        assert validation_result is None
    
    @given(
        email=valid_email_strategy(),
        password=valid_password_strategy(),
        phone=valid_phone_strategy()
    )
    @settings(max_examples=10, deadline=5000)
    def test_property_password_hashing_consistency(self, email, password, phone):
        """
        Property: For any password, hashing should be consistent - the same password
        should always verify against its hash, but different passwords should not.
        
        **Validates: Requirements 2.6**
        """
        assume(len(email) <= 255)
        assume(len(phone) <= 20)
        assume('@' in email and '.' in email)
        
        # Register user
        user = self.auth_service.register_user(email, password, phone)
        assert user is not None
        
        # Original password should verify
        assert self.user_service.verify_password(password, user.password_hash)
        
        # Wrong password should not verify
        wrong_password = password + "wrong"
        assert not self.user_service.verify_password(wrong_password, user.password_hash)
        
        # Hash should be different from original password
        assert user.password_hash != password
    
    @given(st.data())
    @settings(max_examples=10, deadline=5000)
    def test_property_guest_cookie_generation_uniqueness(self, data):
        """
        Property: For any number of guest cookie generations, each cookie
        should be unique and have valid format.
        
        **Validates: Requirements 3.1**
        """
        # Generate multiple cookies
        num_cookies = data.draw(st.integers(min_value=2, max_value=10))
        cookies = []
        
        for _ in range(num_cookies):
            cookie_data = self.auth_service.generate_guest_cookie()
            assert cookie_data is not None
            assert "cookie" in cookie_data
            assert "expires_at" in cookie_data
            
            cookie = cookie_data["cookie"]
            expires_at = cookie_data["expires_at"]
            
            # Validate cookie format
            assert self.auth_service.validate_guest_cookie(cookie)
            assert cookie.startswith("guest_")
            assert len(cookie) == 38  # "guest_" + 32 characters
            assert expires_at > datetime.utcnow()
            
            cookies.append(cookie)
        
        # All cookies should be unique
        assert len(set(cookies)) == len(cookies)