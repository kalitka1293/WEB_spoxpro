"""
Database initialization and session management for spoXpro backend.

This module provides comprehensive database initialization, session management,
and health check functionality for the spoXpro e-commerce backend.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text, event
from typing import Optional, Generator, Dict, Any
from pathlib import Path

from config.database import (
    engine, 
    SessionLocal, 
    Base, 
    create_database_tables, 
    check_database_connection,
    get_database_info
)
from config.settings import get_settings
from logs.log_store import get_logger

logger = get_logger(__name__)
settings = get_settings()


def init_database() -> bool:
    """
    Initialize the database by creating all tables and setting up constraints.
    
    This function:
    1. Checks database connection
    2. Creates database directory if needed
    3. Sets up SQLite pragmas for foreign key constraints
    4. Creates all database tables
    5. Logs initialization status
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    try:
        logger.info("Starting database initialization...")
        
        # Ensure database directory exists for SQLite
        if "sqlite" in settings.database_url:
            db_path = settings.database_url.replace("sqlite:///", "")
            if db_path != ":memory:":
                db_dir = os.path.dirname(db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                    logger.info(f"Created database directory: {db_dir}")
        
        # Check database connection first
        if not check_database_connection():
            logger.error("Database connection failed during initialization")
            return False
        
        # Set up SQLite foreign key constraints
        _setup_sqlite_constraints()
        
        # Import all models to ensure they are registered
        _import_all_models()
        
        # Create all tables
        create_database_tables()
        
        # Verify table creation
        if not _verify_tables_created():
            logger.error("Table verification failed after creation")
            return False
        
        # Log database info
        db_info = get_database_info()
        logger.info(f"Database initialized successfully: {db_info}")
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        return False


def _setup_sqlite_constraints():
    """Set up SQLite foreign key constraints and other pragmas."""
    if "sqlite" in settings.database_url:
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            # Set synchronous mode for better performance
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
        
        # Also set pragmas on the current connection
        try:
            with engine.connect() as connection:
                connection.execute(text("PRAGMA foreign_keys=ON"))
                connection.execute(text("PRAGMA journal_mode=WAL"))
                connection.execute(text("PRAGMA synchronous=NORMAL"))
                connection.commit()
        except Exception as e:
            logger.warning(f"Could not set SQLite pragmas on current connection: {e}")
        
        logger.info("SQLite constraints and pragmas configured")


def _import_all_models():
    """Import all models to ensure they are registered with SQLAlchemy."""
    try:
        # Import all models from the models package
        from db.models import (
            Product, ProductSize, ProductType, Category, SportType, Material,
            User, VerificationCode,
            CartItem, Order, OrderItem
        )
        logger.info("All database models imported successfully")
    except ImportError as e:
        logger.error(f"Failed to import database models: {e}")
        raise


def _verify_tables_created() -> bool:
    """Verify that all expected tables were created."""
    try:
        with engine.connect() as connection:
            # Get list of tables
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = [
                'products', 'product_sizes', 'product_types', 'categories', 
                'sport_types', 'materials', 'users', 'verification_codes',
                'cart_items', 'orders', 'order_items'
            ]
            
            missing_tables = [table for table in expected_tables if table not in tables]
            
            if missing_tables:
                logger.error(f"Missing tables after creation: {missing_tables}")
                return False
            
            logger.info(f"All expected tables created: {tables}")
            return True
            
    except Exception as e:
        logger.error(f"Table verification failed: {e}")
        return False


def get_db_session() -> Session:
    """
    Create and return a new database session.
    
    Returns:
        Session: SQLAlchemy database session
    """
    return SessionLocal()


@contextmanager
def get_db_session_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with automatic cleanup.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        with get_db_session_context() as db:
            # Use db session
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


def close_db_session(db: Session) -> None:
    """
    Close a database session safely.
    
    Args:
        db: SQLAlchemy database session to close
    """
    try:
        db.close()
    except Exception as e:
        logger.error(f"Error closing database session: {e}")


def execute_with_db(func, *args, **kwargs):
    """
    Execute a function with a database session.
    Automatically handles session creation, transaction management, and cleanup.
    
    Args:
        func: Function to execute that takes db as first parameter
        *args: Additional arguments to pass to function
        **kwargs: Additional keyword arguments to pass to function
    
    Returns:
        Result of function execution
        
    Raises:
        Exception: Re-raises any exception from the function after rollback
    """
    with get_db_session_context() as db:
        return func(db, *args, **kwargs)


def execute_transaction(func, *args, **kwargs):
    """
    Execute a function within a database transaction.
    Commits on success, rolls back on failure.
    
    Args:
        func: Function to execute that takes db as first parameter
        *args: Additional arguments to pass to function
        **kwargs: Additional keyword arguments to pass to function
    
    Returns:
        Result of function execution
    """
    db = get_db_session()
    try:
        result = func(db, *args, **kwargs)
        db.commit()
        return result
    except Exception as e:
        logger.error(f"Transaction failed, rolling back: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        close_db_session(db)


def health_check() -> Dict[str, Any]:
    """
    Perform a comprehensive database health check.
    
    Returns:
        dict: Health check results including status, connection info, and diagnostics
    """
    try:
        health_status = {
            "status": "unknown",
            "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
                "health_check", logging.INFO, "", 0, "", (), None
            )) if logger.handlers else None,
            "database_info": {},
            "connection_active": False,
            "tables_exist": False,
            "foreign_keys_enabled": False,
            "diagnostics": {}
        }
        
        # Check basic connection
        connection_ok = check_database_connection()
        health_status["connection_active"] = connection_ok
        
        if not connection_ok:
            health_status["status"] = "unhealthy"
            health_status["diagnostics"]["error"] = "Database connection failed"
            return health_status
        
        # Get database info
        db_info = get_database_info()
        health_status["database_info"] = db_info
        
        # Check if tables exist
        tables_exist = _check_tables_exist()
        health_status["tables_exist"] = tables_exist
        
        # Check foreign key constraints (SQLite specific)
        fk_enabled = _check_foreign_keys_enabled()
        health_status["foreign_keys_enabled"] = fk_enabled
        
        # Perform basic query test
        query_test = _perform_query_test()
        health_status["diagnostics"]["query_test"] = query_test
        
        # Determine overall status
        if connection_ok and tables_exist and query_test["success"]:
            health_status["status"] = "healthy"
        else:
            health_status["status"] = "unhealthy"
            
        return health_status
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
            "connection_active": False,
            "timestamp": None
        }


def _check_tables_exist() -> bool:
    """Check if all expected database tables exist."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = [
                'products', 'product_sizes', 'product_types', 'categories', 
                'sport_types', 'materials', 'users', 'verification_codes',
                'cart_items', 'orders', 'order_items'
            ]
            
            return all(table in tables for table in expected_tables)
            
    except Exception as e:
        logger.error(f"Table existence check failed: {e}")
        return False


def _check_foreign_keys_enabled() -> bool:
    """Check if foreign key constraints are enabled (SQLite specific)."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("PRAGMA foreign_keys"))
            fk_status = result.fetchone()
            return fk_status[0] == 1 if fk_status else False
            
    except Exception as e:
        logger.error(f"Foreign key check failed: {e}")
        return False


def _perform_query_test() -> Dict[str, Any]:
    """Perform a basic query test to verify database functionality."""
    try:
        with engine.connect() as connection:
            # Test basic SELECT
            result = connection.execute(text("SELECT 1 as test_value"))
            test_row = result.fetchone()
            
            if test_row and test_row[0] == 1:
                return {"success": True, "message": "Query test passed"}
            else:
                return {"success": False, "message": "Query test returned unexpected result"}
                
    except Exception as e:
        return {"success": False, "message": f"Query test failed: {str(e)}"}


def reset_database() -> bool:
    """
    Reset the database by dropping and recreating all tables.
    
    WARNING: This will delete all data in the database!
    
    Returns:
        bool: True if reset successful, False otherwise
    """
    try:
        logger.warning("Resetting database - all data will be lost!")
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped")
        
        # Recreate all tables
        success = init_database()
        
        if success:
            logger.info("Database reset completed successfully")
        else:
            logger.error("Database reset failed during reinitialization")
            
        return success
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}", exc_info=True)
        return False


def get_session_factory():
    """
    Get the session factory for dependency injection.
    
    Returns:
        sessionmaker: SQLAlchemy session factory
    """
    return SessionLocal


def create_database_if_not_exists() -> bool:
    """
    Create database file if it doesn't exist (SQLite specific).
    
    Returns:
        bool: True if database exists or was created successfully
    """
    try:
        if "sqlite" in settings.database_url:
            db_path = settings.database_url.replace("sqlite:///", "")
            
            if db_path == ":memory:":
                # In-memory database, always "exists"
                return True
                
            if not os.path.exists(db_path):
                # Create directory if needed
                db_dir = os.path.dirname(db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                
                # Touch the database file
                Path(db_path).touch()
                logger.info(f"Created database file: {db_path}")
                
            return True
        else:
            # For non-SQLite databases, assume they exist or will be created by the server
            return True
            
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        return False