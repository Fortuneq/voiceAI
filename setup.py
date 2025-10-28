#!/usr/bin/env python3
"""
Setup script for VoiceAI Call Analysis System.
"""

import os
import sys
from pathlib import Path


def create_directories():
    """Create necessary directories."""
    directories = [
        "logs",
        "temp_audio",
        "src/__pycache__"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")


def check_requirements():
    """Check if requirements are installed."""
    print("Checking Python requirements...")
    
    required_packages = [
        "google-api-python-client",
        "google-auth-httplib2", 
        "google-auth-oauthlib",
        "gspread",
        "openai",
        "python-dotenv",
        "pydantic",
        "loguru"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True


def check_env_file():
    """Check if .env file exists and has required variables."""
    env_path = Path(".env")
    
    if not env_path.exists():
        print("❌ .env file not found")
        print("📋 Copy .env.example to .env and fill in your credentials")
        return False
    
    print("✅ .env file found")
    
    # Check for required environment variables
    required_vars = [
        "OPENAI_API_KEY",
        "GOOGLE_SERVICE_ACCOUNT_FILE",
        "GOOGLE_DRIVE_FOLDER_ID", 
        "GOOGLE_SPREADSHEET_ID"
    ]
    
    missing_vars = []
    
    with open(env_path) as f:
        env_content = f.read()
        
    for var in required_vars:
        if f"{var}=" not in env_content or f"{var}=your_" in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing or placeholder values: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True


def check_google_credentials():
    """Check if Google service account file exists."""
    from dotenv import load_dotenv
    load_dotenv()
    
    service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    
    if not service_account_file:
        print("❌ GOOGLE_SERVICE_ACCOUNT_FILE not set in .env")
        return False
    
    if not Path(service_account_file).exists():
        print(f"❌ Google service account file not found: {service_account_file}")
        return False
    
    print("✅ Google service account file found")
    return True


def main():
    """Main setup function."""
    print("🛠️  VoiceAI Call Analysis System Setup")
    print("=" * 50)
    
    # Create directories
    print("\n1. Creating directories...")
    create_directories()
    
    # Check requirements
    print("\n2. Checking Python requirements...")
    if not check_requirements():
        print("\n❌ Setup incomplete - install missing packages first")
        sys.exit(1)
    
    # Check .env file
    print("\n3. Checking environment configuration...")
    if not check_env_file():
        print("\n❌ Setup incomplete - configure .env file")
        sys.exit(1)
    
    # Check Google credentials
    print("\n4. Checking Google credentials...")
    if not check_google_credentials():
        print("\n❌ Setup incomplete - configure Google service account")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Test the system: python test_workflow.py")
    print("2. Run health check: python main.py --mode health-check")
    print("3. Start monitoring: python main.py --mode monitor")
    print("\n📚 Documentation: README.md")


if __name__ == "__main__":
    main()