"""
Unit tests for database initialization and session management.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.db.main import (
    init_database,
    health_check,
    get_db_session_context,
    create_database_if_not_exists,
    reset_database,
    _check_tables_exist,
    _check_foreign_keys_enabled,
    _perform_query_test
)
from backend.config.database import Base


class TestDatabaseInitialization:
    """Test database initialization functionality."""
    
    def test_create_database_if_not_exists_sqlite(self):
        """Test creating SQLite database file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            
            with patch('backend.db.main.settings') as mock_settings:
                mock_settings.database_url = f"sqlite:///{db_path}"
                
                # Database file shouldn't exist initially
                assert not os.path.exists(db_path)
                
                # Create database
                result = create_database_if_not_exists()
                
                # Should succeed and create file
                assert result is True
                assert os.path.exists(db_path)
    
    def test_create_database_if_not_exists_memory(self):
        """Test in-memory database creation."""
        with patch('backend.db.main.settings') as mock_settings:
            mock_settings.database_url = "sqlite:///:memory:"
            
            result = create_database_if_not_exists()
            assert result is True
    
    def test_init_database_success(self):
        """Test successful database initialization."""
        with patch('backend.db.main.check_database_connection', return_value=True), \
             patch('backend.db.main._setup_sqlite_constraints'), \
             patch('backend.db.main._import_all_models'), \
             patch('backend.db.main.create_database_tables'), \
             patch('backend.db.main._verify_tables_created', return_value=True), \
             patch('backend.db.main.get_database_info', return_value={"test": "info"}):
            
            result = init_database()
            assert result is True
    
    def test_init_database_connection_failure(self):
        """Test database initialization with connection failure."""
        with patch('backend.db.main.check_database_connection', return_value=False):
            result = init_database()
            assert result is False
    
    def test_init_database_table_verification_failure(self):
        """Test database initialization with table verification failure."""
        with patch('backend.db.main.check_database_connection', return_value=True), \
             patch('backend.db.main._setup_sqlite_constraints'), \
             patch('backend.db.main._import_all_models'), \
             patch('backend.db.main.create_database_tables'), \
             patch('backend.db.main._verify_tables_created', return_value=False):
            
            result = init_database()
            assert result is False
    
    def test_health_check_healthy(self):
        """Test health check with healthy database."""
        with patch('backend.db.main.check_database_connection', return_value=True), \
             patch('backend.db.main.get_database_info', return_value={"test": "info"}), \
             patch('backend.db.main._check_tables_exist', return_value=True), \
             patch('backend.db.main._check_foreign_keys_enabled', return_value=True), \
             patch('backend.db.main._perform_query_test', return_value={"success": True}):
            
            result = health_check()
            
            assert result["status"] == "healthy"
            assert result["connection_active"] is True
            assert result["tables_exist"] is True
            assert result["foreign_keys_enabled"] is True
    
    def test_health_check_unhealthy_connection(self):
        """Test health check with connection failure."""
        with patch('backend.db.main.check_database_connection', return_value=False):
            result = health_check()
            
            assert result["status"] == "unhealthy"
            assert result["connection_active"] is False
    
    def test_health_check_unhealthy_query(self):
        """Test health check with query failure."""
        with patch('backend.db.main.check_database_connection', return_value=True), \
             patch('backend.db.main.get_database_info', return_value={"test": "info"}), \
             patch('backend.db.main._check_tables_exist', return_value=True), \
             patch('backend.db.main._check_foreign_keys_enabled', return_value=True), \
             patch('backend.db.main._perform_query_test', return_value={"success": False}):
            
            result = health_check()
            
            assert result["status"] == "unhealthy"
            assert result["connection_active"] is True
            assert result["tables_exist"] is True
    
    def test_session_context_manager_success(self):
        """Test successful session context manager usage."""
        mock_session = MagicMock()
        
        with patch('backend.db.main.SessionLocal', return_value=mock_session):
            with get_db_session_context() as db:
                assert db == mock_session
                # Simulate some database operation
                db.query.return_value = "test_result"
            
            # Verify session was committed and closed
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()
    
    def test_session_context_manager_exception(self):
        """Test session context manager with exception."""
        mock_session = MagicMock()
        
        with patch('backend.db.main.SessionLocal', return_value=mock_session):
            with pytest.raises(ValueError):
                with get_db_session_context() as db:
                    assert db == mock_session
                    raise ValueError("Test exception")
            
            # Verify session was rolled back and closed
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
    
    def test_check_tables_exist_success(self):
        """Test successful table existence check."""
        expected_tables = [
            'products', 'product_sizes', 'product_types', 'categories', 
            'sport_types', 'materials', 'users', 'verification_codes',
            'cart_items', 'orders', 'order_items'
        ]
        
        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [(table,) for table in expected_tables]
        mock_connection.execute.return_value = mock_result
        
        with patch('backend.db.main.engine') as mock_engine:
            mock_engine.connect.return_value.__enter__.return_value = mock_connection
            
            result = _check_tables_exist()
            assert result is True
    
    def test_check_tables_exist_missing_tables(self):
        """Test table existence check with missing tables."""
        # Only return some tables, not all expected ones
        partial_tables = ['products', 'users']
        
        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [(table,) for table in partial_tables]
        mock_connection.execute.return_value = mock_result
        
        with patch('backend.db.main.engine') as mock_engine:
            mock_engine.connect.return_value.__enter__.return_value = mock_connection
            
            result = _check_tables_exist()
            assert result is False
    
    def test_check_foreign_keys_enabled_true(self):
        """Test foreign key check when enabled."""
        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)  # Foreign keys enabled
        mock_connection.execute.return_value = mock_result
        
        with patch('backend.db.main.engine') as mock_engine:
            mock_engine.connect.return_value.__enter__.return_value = mock_connection
            
            result = _check_foreign_keys_enabled()
            assert result is True
    
    def test_check_foreign_keys_enabled_false(self):
        """Test foreign key check when disabled."""
        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (0,)  # Foreign keys disabled
        mock_connection.execute.return_value = mock_result
        
        with patch('backend.db.main.engine') as mock_engine:
            mock_engine.connect.return_value.__enter__.return_value = mock_connection
            
            result = _check_foreign_keys_enabled()
            assert result is False
    
    def test_perform_query_test_success(self):
        """Test successful query test."""
        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)  # Expected test value
        mock_connection.execute.return_value = mock_result
        
        with patch('backend.db.main.engine') as mock_engine:
            mock_engine.connect.return_value.__enter__.return_value = mock_connection
            
            result = _perform_query_test()
            assert result["success"] is True
            assert "passed" in result["message"]
    
    def test_perform_query_test_failure(self):
        """Test query test with exception."""
        mock_connection = MagicMock()
        mock_connection.execute.side_effect = Exception("Database error")
        
        with patch('backend.db.main.engine') as mock_engine:
            mock_engine.connect.return_value.__enter__.return_value = mock_connection
            
            result = _perform_query_test()
            assert result["success"] is False
            assert "failed" in result["message"]
    
    def test_reset_database_success(self):
        """Test successful database reset."""
        with patch('backend.db.main.Base') as mock_base, \
             patch('backend.db.main.init_database', return_value=True):
            
            result = reset_database()
            
            assert result is True
            mock_base.metadata.drop_all.assert_called_once()
    
    def test_reset_database_failure(self):
        """Test database reset with failure."""
        with patch('backend.db.main.Base') as mock_base, \
             patch('backend.db.main.init_database', return_value=False):
            
            result = reset_database()
            
            assert result is False
            mock_base.metadata.drop_all.assert_called_once()


class TestDatabaseIntegration:
    """Integration tests for database functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        # Use in-memory database to avoid file permission issues
        test_engine = create_engine("sqlite:///:memory:", echo=False)
        TestSession = sessionmaker(bind=test_engine)
        
        # Create tables
        Base.metadata.create_all(bind=test_engine)
        
        yield test_engine, TestSession
    
    def test_database_session_transaction(self, temp_db):
        """Test database session transaction handling."""
        engine, SessionClass = temp_db
        
        # Test successful transaction
        session = SessionClass()
        try:
            result = session.execute(text("SELECT 1 as test"))
            assert result.fetchone()[0] == 1
            session.commit()
        finally:
            session.close()
        
        # Test rollback on exception
        session = SessionClass()
        try:
            session.execute(text("SELECT 1 as test"))
            # Simulate an error
            session.rollback()
        finally:
            session.close()