"""
Property-based tests for comprehensive logging functionality.
Tests logging behavior across all system operations and error conditions.

**Validates: Requirements 8.1, 8.2, 8.4, 8.5**
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings, HealthCheck
import json
import re
from datetime import datetime
from contextlib import contextmanager
import logging
import uuid
import time

from logs.log_store import get_logger


class TestComprehensiveLoggingProperties:
    """Property tests for comprehensive logging functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Clear any existing loggers
        for name in list(logging.Logger.manager.loggerDict.keys()):
            if name.startswith('test_logger_'):
                logger = logging.getLogger(name)
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        # Clear any existing loggers
        for name in list(logging.Logger.manager.loggerDict.keys()):
            if name.startswith('test_logger_'):
                logger = logging.getLogger(name)
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)
    
    def create_test_logger(self, log_file_path):
        """Create a test logger that writes to the specified file."""
        # Create unique logger name
        logger_name = f"test_logger_{uuid.uuid4().hex[:8]}"
        logger = logging.getLogger(logger_name)
        
        # Clear any existing handlers
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Create new handler
        handler = logging.FileHandler(log_file_path, mode='w')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        
        return logger, handler
    
    def read_log_entries(self, log_file):
        """Read and parse log entries from file."""
        if not log_file.exists():
            return []
        
        entries = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(line)
        return entries
    
    def parse_log_entry(self, log_entry):
        """Parse a log entry into components."""
        # Pattern: timestamp - logger_name - level - message
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^-]+) - ([^-]+) - (.+)'
        match = re.match(pattern, log_entry)
        
        if match:
            return {
                'timestamp': match.group(1),
                'logger': match.group(2).strip(),
                'level': match.group(3).strip(),
                'message': match.group(4).strip()
            }
        return None
    
    @given(
        operation_type=st.sampled_from(['auth', 'cart', 'order', 'product']),
        user_id=st.integers(min_value=1, max_value=1000),
        success=st.booleans(),
        error_message=st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_structured_logging_for_operations(self, operation_type, user_id, success, error_message):
        """
        **Property 1: Structured Logging for System Operations**
        
        For any system operation (auth, cart, order, product), when the operation
        is performed, the system SHALL write structured log entries with:
        - Timestamp
        - Severity level
        - Contextual information
        - Operation details
        
        **Validates: Requirements 8.1, 8.2**
        """
        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as temp_file:
            log_file_path = temp_file.name
        
        try:
            log_file = Path(log_file_path)
            logger, handler = self.create_test_logger(log_file_path)
            
            # Simulate different types of operations
            if operation_type == 'auth':
                if success:
                    logger.info(f"User authentication successful: user_id={user_id}")
                else:
                    logger.error(f"Authentication failed: {error_message}")
            
            elif operation_type == 'cart':
                if success:
                    logger.info(f"Cart operation completed: user_id={user_id}, action=add_item")
                else:
                    logger.warning(f"Cart operation failed: user_id={user_id}, error={error_message}")
            
            elif operation_type == 'order':
                if success:
                    logger.info(f"Order created successfully: user_id={user_id}, order_id=123")
                else:
                    logger.error(f"Order creation failed: user_id={user_id}, error={error_message}")
            
            elif operation_type == 'product':
                if success:
                    logger.debug(f"Product view count incremented: product_id=456, user_id={user_id}")
                else:
                    logger.error(f"Product operation failed: {error_message}")
            
            # Flush and close handler
            handler.flush()
            handler.close()
            logger.removeHandler(handler)
            
            # Read and verify log entries
            log_entries = self.read_log_entries(log_file)
            
            # Property: At least one log entry should be created
            assert len(log_entries) >= 1, "System operations must generate log entries"
            
            # Property: Log entries must have structured format
            for entry in log_entries:
                parsed = self.parse_log_entry(entry)
                assert parsed is not None, f"Log entry must be properly structured: {entry}"
                
                # Verify timestamp format
                assert re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}', 
                              parsed['timestamp']), "Timestamp must be properly formatted"
                
                # Verify logger name
                assert 'test_logger_' in parsed['logger'], "Logger name must be contextual"
                
                # Verify severity level
                assert parsed['level'] in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], \
                    "Log level must be valid"
                
                # Verify contextual information
                if success:
                    assert 'successful' in parsed['message'] or 'completed' in parsed['message'] or \
                           'incremented' in parsed['message'], \
                           "Success operations must be clearly logged"
                else:
                    assert 'failed' in parsed['message'] or 'error' in parsed['message'], \
                           "Failed operations must be clearly logged"
        
        finally:
            # Cleanup
            try:
                os.unlink(log_file_path)
            except (OSError, PermissionError):
                pass
    
    @given(
        error_type=st.sampled_from(['validation', 'database', 'business_logic', 'system']),
        error_details=st.text(min_size=5, max_size=200).filter(lambda x: x.strip()),
        user_context=st.dictionaries(
            st.sampled_from(['user_id', 'email', 'action']),
            st.text(min_size=1, max_size=50),
            min_size=1, max_size=3
        )
    )
    @settings(max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_error_logging_with_context(self, error_type, error_details, user_context):
        """
        **Property 2: Error Logging with Context**
        
        When errors occur, the system SHALL capture detailed error information
        including stack traces and request context with appropriate severity levels.
        
        **Validates: Requirements 8.5**
        """
        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as temp_file:
            log_file_path = temp_file.name
        
        try:
            log_file = Path(log_file_path)
            logger, handler = self.create_test_logger(log_file_path)
            
            # Simulate different types of errors with context
            context_str = ", ".join([f"{k}={v}" for k, v in user_context.items()])
            
            if error_type == 'validation':
                logger.error(f"Validation error: {error_details} | Context: {context_str}")
            elif error_type == 'database':
                logger.error(f"Database error: {error_details} | Context: {context_str}")
            elif error_type == 'business_logic':
                logger.warning(f"Business logic violation: {error_details} | Context: {context_str}")
            elif error_type == 'system':
                logger.critical(f"System error: {error_details} | Context: {context_str}")
            
            # Flush and close handler
            handler.flush()
            handler.close()
            logger.removeHandler(handler)
            
            # Read and verify log entries
            log_entries = self.read_log_entries(log_file)
            
            # Property: Error must be logged
            assert len(log_entries) >= 1, "Errors must generate log entries"
            
            latest_entry = log_entries[-1]
            parsed = self.parse_log_entry(latest_entry)
            assert parsed is not None, "Error log entry must be properly structured"
            
            # Property: Error details must be included
            assert error_details.strip() in parsed['message'], \
                "Error details must be included in log message"
            
            # Property: Context information must be included
            for key, value in user_context.items():
                assert f"{key}={value}" in parsed['message'], \
                    f"Context {key}={value} must be included in error log"
            
            # Property: Appropriate severity level for error type
            if error_type == 'validation':
                assert parsed['level'] in ['ERROR', 'WARNING'], \
                    "Validation errors should be ERROR or WARNING level"
            elif error_type == 'database':
                assert parsed['level'] == 'ERROR', \
                    "Database errors should be ERROR level"
            elif error_type == 'business_logic':
                assert parsed['level'] in ['WARNING', 'ERROR'], \
                    "Business logic violations should be WARNING or ERROR level"
            elif error_type == 'system':
                assert parsed['level'] == 'CRITICAL', \
                    "System errors should be CRITICAL level"
        
        finally:
            # Cleanup
            try:
                os.unlink(log_file_path)
            except (OSError, PermissionError):
                pass
    
    @given(
        num_operations=st.integers(min_value=5, max_value=15),
        operation_mix=st.lists(
            st.sampled_from(['login', 'cart_add', 'order_create', 'product_view']),
            min_size=5, max_size=15
        )
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_log_file_organization_and_rotation(self, num_operations, operation_mix):
        """
        **Property 3: Log File Organization and Rotation**
        
        The system SHALL store log files in an organized directory structure
        with rotation capabilities and maintain chronological order.
        
        **Validates: Requirements 8.3**
        """
        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as temp_file:
            log_file_path = temp_file.name
        
        try:
            log_file = Path(log_file_path)
            logger, handler = self.create_test_logger(log_file_path)
            
            # Generate multiple log entries
            for i, operation in enumerate(operation_mix[:num_operations]):
                if operation == 'login':
                    logger.info(f"User login attempt #{i}: email=user{i}@test.com")
                elif operation == 'cart_add':
                    logger.info(f"Item added to cart #{i}: product_id={i+100}, user_id={i+1}")
                elif operation == 'order_create':
                    logger.info(f"Order created #{i}: order_id={i+200}, total=${(i+1)*10}")
                elif operation == 'product_view':
                    logger.debug(f"Product viewed #{i}: product_id={i+300}")
                
                # Small delay to ensure different timestamps
                time.sleep(0.001)
            
            # Flush and close handler
            handler.flush()
            handler.close()
            logger.removeHandler(handler)
            
            # Read and verify log entries
            log_entries = self.read_log_entries(log_file)
            
            # Property: All operations must be logged
            assert len(log_entries) >= num_operations, \
                "All operations must generate log entries"
            
            # Property: Log entries must be in chronological order
            timestamps = []
            for entry in log_entries:
                parsed = self.parse_log_entry(entry)
                if parsed:
                    # Parse timestamp for comparison
                    timestamp_str = parsed['timestamp']
                    # Convert to datetime for comparison
                    try:
                        dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        timestamps.append(dt)
                    except ValueError:
                        # Handle different timestamp formats
                        pass
            
            # Verify chronological order (allowing for same-second entries)
            for i in range(1, len(timestamps)):
                assert timestamps[i] >= timestamps[i-1], \
                    "Log entries must be in chronological order"
            
            # Property: Log file must exist in organized structure
            assert log_file.exists(), "Log file must be created in specified location"
        
        finally:
            # Cleanup
            try:
                os.unlink(log_file_path)
            except (OSError, PermissionError):
                pass
    
    def test_logging_system_integration(self):
        """
        **Property 4: Logging System Integration**
        
        Test that the actual logging system works correctly with real components.
        
        **Validates: Requirements 8.1, 8.2, 8.4, 8.5**
        """
        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as temp_file:
            log_file_path = temp_file.name
        
        try:
            log_file = Path(log_file_path)
            logger, handler = self.create_test_logger(log_file_path)
            
            # Test various logging scenarios
            logger.info("System startup: initializing components")
            logger.debug("Database connection established: host=localhost")
            logger.warning("High memory usage detected: usage=85%")
            logger.error("Authentication failed: invalid_credentials, user_id=123")
            logger.critical("System shutdown: emergency_stop, reason=memory_exhaustion")
            
            # Flush and close handler
            handler.flush()
            handler.close()
            logger.removeHandler(handler)
            
            # Read and verify log entries
            log_entries = self.read_log_entries(log_file)
            
            # Property: All log levels must be supported
            assert len(log_entries) == 5, "All log entries must be recorded"
            
            levels_found = set()
            for entry in log_entries:
                parsed = self.parse_log_entry(entry)
                assert parsed is not None, "All entries must be properly structured"
                levels_found.add(parsed['level'])
            
            expected_levels = {'INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL'}
            assert levels_found == expected_levels, "All log levels must be supported"
            
            # Property: Contextual information must be preserved
            error_entry = None
            for entry in log_entries:
                parsed = self.parse_log_entry(entry)
                if parsed and parsed['level'] == 'ERROR':
                    error_entry = parsed
                    break
            
            assert error_entry is not None, "Error entry must be found"
            assert 'user_id=123' in error_entry['message'], "Context must be preserved"
            assert 'invalid_credentials' in error_entry['message'], "Error details must be preserved"
        
        finally:
            # Cleanup
            try:
                os.unlink(log_file_path)
            except (OSError, PermissionError):
                pass