#!/usr/bin/env python3
"""
Simple admin user creation script that bypasses bcrypt issues.
"""

import sys
import hashlib
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from database_service import DatabaseService
from loguru import logger

def simple_hash_password(password: str) -> str:
    """Simple password hashing using SHA256 - NOT SECURE FOR PRODUCTION."""
    # This is a temporary solution - in production use proper bcrypt
    salt = "voiceai_salt_12345"  # Fixed salt for simplicity
    return hashlib.sha256((password + salt).encode()).hexdigest()

def create_admin_simple():
    """Create admin user with simple hashing."""
    print("Creating admin user with simple hashing...")
    
    try:
        db_service = DatabaseService()
        
        # Check if admin already exists
        existing_admin = db_service.get_user_by_username("admin")
        if existing_admin:
            print("Admin user already exists!")
            return True
        
        # Simple password hash
        password_hash = simple_hash_password("admin123")
        
        # Create user directly using database session
        session = db_service.get_session()
        try:
            from database_models import User
            admin_user = User(
                username="admin",
                email="admin@voiceai.com",
                password_hash=password_hash,
                role="admin",
                is_active=True
            )
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)
            
            print(f"Admin user created successfully!")
            print(f"Username: admin")
            print(f"Password: admin123")
            print(f"Email: admin@voiceai.com")
            print(f"Role: admin")
            print("\nNOTE: This uses simple password hashing for development only!")
            print("In production, use proper bcrypt hashing.")
            
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating admin user: {e}")
            print(f"Error: {e}")
            return False
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Database error: {e}")
        print(f"Database error: {e}")
        return False

if __name__ == "__main__":
    create_admin_simple()