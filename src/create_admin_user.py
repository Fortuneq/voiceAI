#!/usr/bin/env python3
"""
Create admin user for VoiceAI Call Analysis System.
This script creates the first admin user for accessing the system.
"""

import sys
from pathlib import Path
from getpass import getpass

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from database_service import DatabaseService
from auth_utils import get_password_hash
from config import config
from loguru import logger

def create_admin_user():
    """Create the first admin user."""
    
    print("=== VoiceAI Admin User Creation ===")
    print("This script will create the first admin user for the VoiceAI system.")
    print()
    
    # Initialize database service
    try:
        db_service = DatabaseService()
        logger.info("Database service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database service: {e}")
        print(f"Error: Failed to connect to database: {e}")
        return False
    
    # Check if any admin users already exist
    existing_users = db_service.get_all_users()
    admin_users = [user for user in existing_users if user.role == 'admin']
    
    if admin_users:
        print(f"Admin users already exist in the system:")
        for admin in admin_users:
            print(f"  - {admin.username} ({admin.email}) - Active: {admin.is_active}")
        
        response = input("\nDo you want to create another admin user? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Aborted.")
            return True
    
    # Get user input
    print("\nEnter details for the new admin user:")
    
    username = input("Username: ").strip()
    if not username:
        print("Error: Username cannot be empty")
        return False
    
    # Check if username already exists
    existing_user = db_service.get_user_by_username(username)
    if existing_user:
        print(f"Error: User with username '{username}' already exists")
        return False
    
    email = input("Email: ").strip()
    if not email:
        print("Error: Email cannot be empty")
        return False
    
    # Check if email already exists
    existing_email = db_service.get_user_by_email(email)
    if existing_email:
        print(f"Error: User with email '{email}' already exists")
        return False
    
    # Get password securely
    while True:
        password = getpass("Password: ")
        if len(password) < 6:
            print("Error: Password must be at least 6 characters long")
            continue
        
        password_confirm = getpass("Confirm password: ")
        if password != password_confirm:
            print("Error: Passwords do not match")
            continue
        
        break
    
    # Create user
    try:
        password_hash = get_password_hash(password)
        user = db_service.create_user(
            username=username,
            email=email,
            password_hash=password_hash,
            role='admin'
        )
        
        if user:
            print(f"\nAdmin user created successfully!")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role}")
            print(f"Created at: {user.created_at}")
            print("\nYou can now use these credentials to log in to the VoiceAI dashboard.")
            return True
        else:
            print("Error: Failed to create user")
            return False
            
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        print(f"Error: Failed to create user: {e}")
        return False

def main():
    """Main function."""
    try:
        success = create_admin_user()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()