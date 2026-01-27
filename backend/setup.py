"""
Setup script for spoXpro backend development environment.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    print("🔍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True


def create_virtual_environment():
    """Create Python virtual environment."""
    venv_path = Path("venv")
    if venv_path.exists():
        print("📁 Virtual environment already exists")
        return True
    
    return run_command("python -m venv venv", "Creating virtual environment")


def activate_and_install_dependencies():
    """Install dependencies in virtual environment."""
    # Determine activation script based on OS
    if os.name == 'nt':  # Windows
        activate_script = "venv\\Scripts\\activate"
        pip_command = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        activate_script = "source venv/bin/activate"
        pip_command = "venv/bin/pip"
    
    # Install dependencies
    return run_command(f"{pip_command} install -r requirements.txt", "Installing dependencies")


def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("📁 .env file already exists")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please review and update the .env file with your configuration")
        return True
    else:
        print("❌ .env.example file not found")
        return False


def create_log_directory():
    """Create log directory if it doesn't exist."""
    log_dir = Path("logs/log_file")
    log_dir.mkdir(parents=True, exist_ok=True)
    print("✅ Log directory created")
    return True


def run_initial_tests():
    """Run basic tests to verify setup."""
    print("🧪 Running initial tests...")
    
    # Test imports
    try:
        import fastapi
        import sqlalchemy
        import pydantic
        print("✅ All required packages imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 Setting up spoXpro backend development environment")
    print("=" * 50)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Creating virtual environment", create_virtual_environment),
        ("Installing dependencies", activate_and_install_dependencies),
        ("Creating environment file", create_env_file),
        ("Creating log directory", create_log_directory),
        ("Running initial tests", run_initial_tests)
    ]
    
    failed_steps = []
    
    for step_name, step_function in steps:
        if not step_function():
            failed_steps.append(step_name)
    
    print("\n" + "=" * 50)
    
    if failed_steps:
        print("❌ Setup completed with errors:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\nPlease fix the errors and run setup again.")
        return False
    else:
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Review and update the .env file")
        print("2. Activate virtual environment:")
        if os.name == 'nt':
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        print("3. Run the application:")
        print("   python -m backend.main")
        print("4. Visit http://localhost:8000/docs for API documentation")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)