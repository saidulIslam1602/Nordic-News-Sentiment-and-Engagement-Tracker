#!/usr/bin/env python3
"""
Project Setup Script

Sets up the Nordic News Sentiment & Engagement Tracker project
with all necessary dependencies and initial configuration.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    
    # Upgrade pip first
    if not run_command("pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        return False
    
    return True

def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    
    directories = [
        "data",
        "logs",
        "backups",
        "exports"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    return True

def setup_environment():
    """Set up environment configuration."""
    print("⚙️ Setting up environment...")
    
    # Copy example environment file if it doesn't exist
    if not os.path.exists(".env"):
        if os.path.exists("env.example"):
            shutil.copy("env.example", ".env")
            print("✅ Created .env file from template")
        else:
            print("⚠️ No env.example file found")
    
    return True

def initialize_database():
    """Initialize the database with sample data."""
    print("🗄️ Initializing database...")
    
    try:
        # Import and run database initialization
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from scripts.init_database import main as init_db
        init_db()
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def run_tests():
    """Run the test suite."""
    print("🧪 Running tests...")
    
    if not run_command("python -m pytest tests/ -v", "Running tests"):
        print("⚠️ Some tests failed, but continuing with setup")
        return True
    
    return True

def main():
    """Main setup function."""
    print("🚀 Setting up Nordic News Sentiment & Engagement Tracker")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        sys.exit(1)
    
    # Run tests
    if not run_tests():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Review the configuration in config/config.yaml")
    print("2. Update .env file with your settings")
    print("3. Run the dashboard: streamlit run dashboard/main.py")
    print("4. Or run the pipeline: python scripts/run_pipeline.py")
    print("\nFor Docker deployment:")
    print("docker-compose up -d")
    print("\nHappy analyzing! 📊")

if __name__ == "__main__":
    main()