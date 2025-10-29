#!/usr/bin/env python3
"""
Database migration script for VoiceAI Call Analysis System.
This script updates the database schema to include user authentication tables.
"""

import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from database_service import DatabaseService
from database_models import create_tables
from config import config
from loguru import logger

def migrate_database():
    """Migrate database to add authentication tables."""
    
    print("=== VoiceAI Database Migration ===")
    print("This script will update the database schema to include user authentication.")
    print()
    
    try:
        # Initialize database service
        db_service = DatabaseService()
        logger.info("Database service initialized successfully")
        
        # Create/update tables
        print("Creating/updating database tables...")
        create_tables(db_service.engine)
        print("Database tables created/updated successfully!")
        
        # Check if any users exist
        existing_users = db_service.get_all_users()
        
        if not existing_users:
            print("\nNo users found in the database.")
            print("You should run 'python src/create_admin_user.py' to create the first admin user.")
        else:
            print(f"\nFound {len(existing_users)} existing users in the database.")
            admin_users = [user for user in existing_users if user.role == 'admin']
            if admin_users:
                print(f"Admin users: {len(admin_users)}")
            else:
                print("Warning: No admin users found. Run 'python src/create_admin_user.py' to create one.")
        
        print("\nMigration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"Error: Migration failed: {e}")
        return False

def main():
    """Main function."""
    try:
        success = migrate_database()
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