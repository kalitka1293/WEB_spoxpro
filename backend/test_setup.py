#!/usr/bin/env python3
"""
Test script to verify the spoXpro backend setup is working correctly.
"""

import sys
import os

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

def test_imports():
    """Test that all core modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        # Test configuration
        from backend.config.settings import get_settings
        settings = get_settings()
        print(f"✅ Configuration loaded: {settings.app_name}")
        
        # Test logging
        from backend.logs.log_store import setup_logging, get_logger
        setup_logging()
        logger = get_logger(__name__)
        logger.info("Test log message")
        print("✅ Logging system working")
        
        # Test database
        from backend.config.database import check_database_connection
        if check_database_connection():
            print("✅ Database connection working")
        else:
            print("❌ Database connection failed")
            return False
        
        # Test FastAPI app
        from backend.main import app
        print(f"✅ FastAPI app created: {app.title}")
        
        # Test routes
        from backend.routes import auth, user, store
        print("✅ Route modules imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


def test_configuration():
    """Test configuration validation."""
    print("\n🔧 Testing configuration...")
    
    try:
        from backend.config.settings import validate_required_settings
        validate_required_settings()
        print("✅ Configuration validation passed")
        return True
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False


def test_database_init():
    """Test database initialization."""
    print("\n🗄️ Testing database initialization...")
    
    try:
        from backend.db.main import init_database, health_check
        
        if init_database():
            print("✅ Database initialization successful")
        else:
            print("❌ Database initialization failed")
            return False
        
        health = health_check()
        if health["status"] == "healthy":
            print("✅ Database health check passed")
        else:
            print(f"❌ Database health check failed: {health}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def main():
    """Run all setup tests."""
    print("🚀 spoXpro Backend Setup Test")
    print("=" * 40)
    
    tests = [
        ("Import Tests", test_imports),
        ("Configuration Tests", test_configuration),
        ("Database Tests", test_database_init)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Setup is complete and working.")
        print("\nNext steps:")
        print("1. Activate virtual environment: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)")
        print("2. Run the application: python -m backend.main")
        print("3. Visit http://localhost:8000/docs for API documentation")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)