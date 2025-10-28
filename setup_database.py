#!/usr/bin/env python3
"""
Database setup script for VoiceAI Call Analysis System.

This script creates the database tables and can be used to initialize
the database before running the main application.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import config
from src.database_models import create_database_engine, create_tables
from loguru import logger


def main():
    """Initialize the database tables."""
    print("VoiceAI Database Setup")
    print("=" * 50)
    print(f"Database URL: {config.database_url}")
    print(f"Save to database: {config.save_to_database}")
    print(f"Save to sheets: {config.save_to_sheets}")
    print("=" * 50)
    
    if not config.save_to_database:
        print("⚠️  Warning: SAVE_TO_DATABASE is set to false in configuration")
        print("   Database tables will be created but data won't be saved")
        print("")
    
    try:
        # Create database engine
        engine = create_database_engine(config.database_url)
        print("✅ Database engine created successfully")
        
        # Create all tables
        create_tables(engine)
        print("✅ Database tables created successfully")
        
        print("\nDatabase setup complete! You can now run the main application.")
        print("\nTo test the database integration:")
        print("python main.py --mode analyze-file --file-id <your-file-id> --output-file test.json")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        print(f"❌ Database setup failed: {e}")
        print("\nPlease check your database configuration in .env file:")
        print("- DATABASE_URL should point to a valid database")
        print("- For SQLite: sqlite:///./voiceai_calls.db")
        print("- For PostgreSQL: postgresql://username:password@localhost:5432/voiceai_db")
        sys.exit(1)


if __name__ == "__main__":
    main()