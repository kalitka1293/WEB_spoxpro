"""
Test configuration and fixtures for spoXpro backend tests.
"""

import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import uuid

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import Base
from db.models.product import Product, ProductSize, ProductType, Category, SportType, Material


def create_test_db_session() -> Session:
    """
    Create a test database session for property tests.
    This is a function instead of a fixture to work with Hypothesis.
    """
    # Use in-memory SQLite database for faster tests
    test_engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )
    
    # Enable foreign key constraints for SQLite
    from sqlalchemy import event
    
    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create test session
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    return TestSessionLocal()


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """
    Create a temporary test database for regular test functions.
    """
    # Use in-memory database to avoid file permission issues
    test_engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )
    
    # Enable foreign key constraints for SQLite
    from sqlalchemy import event
    
    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create test session
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_helper_data(test_db: Session) -> dict:
    """
    Create sample helper table data for testing.
    """
    # Create helper table records
    product_type = ProductType(name="T-Shirt")
    category = Category(name="Men's Clothing")
    sport_type = SportType(name="Running")
    material = Material(name="Cotton")
    
    test_db.add_all([product_type, category, sport_type, material])
    test_db.commit()
    
    return {
        "product_type_id": product_type.id,
        "category_id": category.id,
        "sport_type_id": sport_type.id,
        "material_id": material.id
    }


def create_sample_helper_data(db: Session) -> dict:
    """
    Create sample helper table data for property tests.
    This is a function instead of a fixture to work with Hypothesis.
    """
    # Create helper table records with unique names to avoid conflicts
    unique_suffix = str(uuid.uuid4())[:8]
    
    product_type = ProductType(name=f"T-Shirt-{unique_suffix}")
    category = Category(name=f"Men's Clothing-{unique_suffix}")
    sport_type = SportType(name=f"Running-{unique_suffix}")
    material = Material(name=f"Cotton-{unique_suffix}")
    
    db.add_all([product_type, category, sport_type, material])
    db.commit()
    
    return {
        "product_type": product_type,
        "category": category,
        "sport_type": sport_type,
        "material": material
    }