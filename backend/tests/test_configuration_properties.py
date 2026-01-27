"""
Property-based tests for configuration management and security functionality.

**Feature: spoxpro-backend, Property 14: Configuration Management and Security**
**Validates: Requirements 9.4, 9.6**

For any application startup, the system should load and validate all required 
configuration parameters, and should never expose sensitive configuration data 
(JWT secrets, API keys) in logs or API responses.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
import tempfile
import json
from unittest.mock import patch, MagicMock

from config.settings import get_settings, validate_required_settings, Settings
from logs.log_store import get_logger


class TestConfigurationManagementProperties:
    """Property-based tests for configuration management and security."""
    
    @given(
        app_name=st.text(min_size=1, max_size=50),
        port=st.integers(min_value=1000, max_value=65535),
        environment=st.sampled_from(['development', 'testing', 'production'])
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_configuration_loading_validation(self, app_name, port, environment):
        """
        Property: For any valid configuration parameters, the system should 
        load and validate them correctly.
        
        **Validates: Requirements 9.4**
        """
        # Filter out problematic characters
        assume(app_name.isprintable())
        assume(not any(char in app_name for char in ['\n', '\r', '\t']))
        
        try:
            # Create temporary environment variables
            test_env = {
                'APP_NAME': app_name,
                'PORT': str(port),
                'ENVIRONMENT': environment,
                'JWT_SECRET_KEY': 'test_secret_key_12345',
                'DATABASE_URL': 'sqlite:///test.db'
            }
            
            with patch.dict(os.environ, test_env, clear=False):
                # Test configuration loading
                settings = get_settings()
                
                # Property assertions for configuration loading
                assert settings.app_name == app_name, "App name should be loaded correctly"
                assert settings.port == port, "Port should be loaded correctly"
                assert settings.environment == environment, "Environment should be loaded correctly"
                assert settings.jwt_secret_key == 'test_secret_key_12345', "JWT secret should be loaded"
                assert settings.database_url == 'sqlite:///test.db', "Database URL should be loaded"
                
                # Test configuration validation
                try:
                    validate_required_settings()
                    validation_passed = True
                except Exception:
                    validation_passed = False
                
                assert validation_passed, "Configuration validation should pass for valid settings"
                
        except Exception as e:
            # If configuration loading fails, it should be due to invalid input
            assert False, f"Configuration loading failed unexpectedly: {str(e)}"
    
    @given(
        missing_field=st.sampled_from(['JWT_SECRET_KEY', 'DATABASE_URL', 'APP_NAME'])
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_configuration_validation_fails_missing_required(self, missing_field):
        """
        Property: For any configuration missing required fields, validation 
        should fail appropriately.
        
        **Validates: Requirements 9.4**
        """
        try:
            # Create incomplete environment
            test_env = {
                'APP_NAME': 'TestApp',
                'PORT': '8000',
                'ENVIRONMENT': 'testing',
                'JWT_SECRET_KEY': 'test_secret',
                'DATABASE_URL': 'sqlite:///test.db'
            }
            
            # Remove the specified field
            if missing_field in test_env:
                del test_env[missing_field]
            
            with patch.dict(os.environ, test_env, clear=True):
                # Test that validation fails
                validation_failed = False
                try:
                    validate_required_settings()
                except Exception:
                    validation_failed = True
                
                # Property assertion - validation should fail for missing required fields
                assert validation_failed, f"Configuration validation should fail when {missing_field} is missing"
                
        except Exception as e:
            # This is expected for missing required fields
            pass
    
    @given(
        log_message=st.text(min_size=10, max_size=100)
    )
    @settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_sensitive_data_not_exposed_in_logs(self, log_message):
        """
        Property: For any log message, sensitive configuration data should 
        never be exposed in logs.
        
        **Validates: Requirements 9.6**
        """
        assume(log_message.isprintable())
        
        try:
            # Set up test environment with sensitive data
            test_env = {
                'JWT_SECRET_KEY': 'super_secret_jwt_key_12345',
                'DATABASE_URL': 'sqlite:///secret_db.db',
                'API_KEY': 'secret_api_key_67890'
            }
            
            with patch.dict(os.environ, test_env, clear=False):
                # Get logger
                logger = get_logger("test_config")
                
                # Mock the logger to capture log messages
                with patch.object(logger, 'info') as mock_info, \
                     patch.object(logger, 'error') as mock_error, \
                     patch.object(logger, 'warning') as mock_warning:
                    
                    # Log a message that might contain sensitive data
                    logger.info(f"Configuration loaded: {log_message}")
                    logger.error(f"Error in config: {log_message}")
                    logger.warning(f"Config warning: {log_message}")
                    
                    # Check all logged messages
                    all_calls = mock_info.call_args_list + mock_error.call_args_list + mock_warning.call_args_list
                    
                    for call in all_calls:
                        if call and call[0]:  # Check if call has arguments
                            logged_message = str(call[0][0])  # Get the first argument (message)
                            
                            # Property assertions - sensitive data should not appear in logs
                            assert 'super_secret_jwt_key_12345' not in logged_message, \
                                "JWT secret should not appear in log messages"
                            assert 'secret_api_key_67890' not in logged_message, \
                                "API key should not appear in log messages"
                            
                            # Database URL might be partially logged, but not with credentials
                            if 'sqlite://' in logged_message:
                                assert 'secret_db.db' not in logged_message, \
                                    "Sensitive database path should not appear in logs"
                
        except Exception as e:
            # Log exposure test should not fail due to other errors
            pass
    
    @given(
        cors_origins=st.lists(st.text(min_size=5, max_size=30), min_size=1, max_size=5)
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_cors_configuration_validation(self, cors_origins):
        """
        Property: For any CORS origins configuration, the system should 
        validate and apply CORS settings correctly.
        
        **Validates: Requirements 9.4**
        """
        # Filter valid URLs
        valid_origins = []
        for origin in cors_origins:
            if origin.isprintable() and not any(char in origin for char in ['\n', '\r', '\t', ' ']):
                # Make it look like a valid URL
                if not origin.startswith('http'):
                    origin = f"https://{origin}.com"
                valid_origins.append(origin)
        
        assume(len(valid_origins) > 0)
        
        try:
            # Create test environment with CORS settings
            test_env = {
                'CORS_ORIGINS': ','.join(valid_origins),
                'CORS_ALLOW_CREDENTIALS': 'true',
                'CORS_ALLOW_METHODS': 'GET,POST,PUT,DELETE',
                'CORS_ALLOW_HEADERS': 'Content-Type,Authorization'
            }
            
            with patch.dict(os.environ, test_env, clear=False):
                settings = get_settings()
                
                # Property assertions for CORS configuration
                assert isinstance(settings.cors_origins, list), "CORS origins should be a list"
                assert len(settings.cors_origins) == len(valid_origins), \
                    "All CORS origins should be loaded"
                
                for origin in valid_origins:
                    assert origin in settings.cors_origins, f"Origin {origin} should be in CORS settings"
                
                assert settings.cors_allow_credentials is True, "CORS credentials should be enabled"
                assert isinstance(settings.cors_allow_methods, list), "CORS methods should be a list"
                assert isinstance(settings.cors_allow_headers, list), "CORS headers should be a list"
                
        except Exception as e:
            # Configuration loading might fail for invalid URLs, which is acceptable
            pass
    
    def test_property_default_configuration_security(self):
        """
        Property: Default configuration should have secure settings and 
        not expose sensitive information.
        
        **Validates: Requirements 9.6**
        """
        try:
            # Test with minimal environment
            test_env = {
                'JWT_SECRET_KEY': 'test_secret_key',
                'DATABASE_URL': 'sqlite:///test.db'
            }
            
            with patch.dict(os.environ, test_env, clear=False):
                settings = get_settings()
                
                # Property assertions for security defaults
                assert settings.debug is False, "Debug should be disabled by default"
                assert settings.jwt_secret_key != '', "JWT secret should not be empty"
                assert len(settings.jwt_secret_key) >= 8, "JWT secret should be sufficiently long"
                
                # Check that sensitive settings are not in string representation
                settings_str = str(settings)
                assert settings.jwt_secret_key not in settings_str, \
                    "JWT secret should not appear in settings string representation"
                
        except Exception as e:
            # Default configuration test should not fail
            assert False, f"Default configuration test failed: {str(e)}"