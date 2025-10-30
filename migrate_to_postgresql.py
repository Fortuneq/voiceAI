#!/usr/bin/env python3
"""
Migration script from SQLite to PostgreSQL.
Migrates both schema and data.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List
import traceback
from datetime import datetime

from loguru import logger
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database_models import Base, User, Manager, CallRecord, ChecklistAnalysis, AIAnalysis, LegacyQualityScore, ProcessedFile
from database_service import DatabaseService


class PostgreSQLMigrator:
    """Migrate from SQLite to PostgreSQL."""
    
    def __init__(self, sqlite_url: str, postgres_url: str, postgres_db_name: str):
        self.sqlite_url = sqlite_url
        self.postgres_url = postgres_url
        self.postgres_db_name = postgres_db_name
        
        self.sqlite_engine = None
        self.postgres_engine = None
        self.sqlite_session = None
        self.postgres_session = None
    
    def migrate(self):
        """Execute full migration process."""
        try:
            logger.info("Starting migration from SQLite to PostgreSQL")
            
            # Step 1: Create PostgreSQL database if it doesn't exist
            self._create_postgres_database()
            
            # Step 2: Connect to both databases
            self._connect_databases()
            
            # Step 3: Create tables in PostgreSQL
            self._create_postgres_tables()
            
            # Step 4: Migrate data
            self._migrate_data()
            
            # Step 5: Verify migration
            self._verify_migration()
            
            logger.info("Migration completed successfully!")
            print("✅ Migration from SQLite to PostgreSQL completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            logger.error(traceback.format_exc())
            print(f"❌ Migration failed: {e}")
            raise
        finally:
            self._close_connections()
    
    def _create_postgres_database(self):
        """Create PostgreSQL database if it doesn't exist."""
        try:
            logger.info(f"Creating PostgreSQL database: {self.postgres_db_name}")
            
            # Parse connection URL to get connection details
            # Format: postgresql://username:password@host:port/dbname
            url_parts = self.postgres_url.replace('postgresql://', '').split('/')
            connection_part = url_parts[0]
            
            if '@' in connection_part:
                auth_part, host_part = connection_part.split('@')
                if ':' in auth_part:
                    username, password = auth_part.split(':')
                else:
                    username = auth_part
                    password = ''
            else:
                host_part = connection_part
                username = 'postgres'
                password = ''
            
            if ':' in host_part:
                host, port = host_part.split(':')
            else:
                host = host_part
                port = '5432'
            
            # Connect to PostgreSQL server (not specific database)
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                database='postgres'  # Connect to default database
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                (self.postgres_db_name,)
            )
            exists = cursor.fetchone()
            
            if not exists:
                logger.info(f"Database {self.postgres_db_name} doesn't exist, creating...")
                cursor.execute(f'CREATE DATABASE "{self.postgres_db_name}"')
                logger.info(f"Created database: {self.postgres_db_name}")
            else:
                logger.info(f"Database {self.postgres_db_name} already exists")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error creating PostgreSQL database: {e}")
            raise
    
    def _connect_databases(self):
        """Connect to both SQLite and PostgreSQL databases."""
        try:
            logger.info("Connecting to databases")
            
            # Connect to SQLite
            self.sqlite_engine = create_engine(self.sqlite_url)
            SQLiteSession = sessionmaker(bind=self.sqlite_engine)
            self.sqlite_session = SQLiteSession()
            logger.info("Connected to SQLite database")
            
            # Connect to PostgreSQL
            full_postgres_url = f"{self.postgres_url}/{self.postgres_db_name}"
            self.postgres_engine = create_engine(full_postgres_url)
            PostgresSession = sessionmaker(bind=self.postgres_engine)
            self.postgres_session = PostgresSession()
            logger.info("Connected to PostgreSQL database")
            
        except Exception as e:
            logger.error(f"Error connecting to databases: {e}")
            raise
    
    def _create_postgres_tables(self):
        """Create all tables in PostgreSQL."""
        try:
            logger.info("Creating tables in PostgreSQL")
            
            # Drop all tables if they exist (clean slate)
            Base.metadata.drop_all(self.postgres_engine)
            logger.info("Dropped existing tables (if any)")
            
            # Create all tables
            Base.metadata.create_all(self.postgres_engine)
            logger.info("Created all tables in PostgreSQL")
            
        except Exception as e:
            logger.error(f"Error creating PostgreSQL tables: {e}")
            raise
    
    def _migrate_data(self):
        """Migrate data from SQLite to PostgreSQL."""
        try:
            logger.info("Starting data migration")
            
            # Define migration order (respecting foreign key dependencies)
            migration_order = [
                (User, "users"),
                (Manager, "managers"),
                (ProcessedFile, "processed_files"),
                (CallRecord, "call_records"),
                (ChecklistAnalysis, "checklist_analysis"),
                (AIAnalysis, "ai_analysis"),
                (LegacyQualityScore, "legacy_quality_scores")
            ]
            
            for model_class, table_name in migration_order:
                self._migrate_table(model_class, table_name)
            
            logger.info("Data migration completed")
            
        except Exception as e:
            logger.error(f"Error migrating data: {e}")
            raise
    
    def _migrate_table(self, model_class, table_name: str):
        """Migrate data for a specific table."""
        try:
            logger.info(f"Migrating table: {table_name}")
            
            # Get all records from SQLite
            sqlite_records = self.sqlite_session.query(model_class).all()
            record_count = len(sqlite_records)
            
            if record_count == 0:
                logger.info(f"No data to migrate for table {table_name}")
                return
            
            logger.info(f"Found {record_count} records in {table_name}")
            
            # Migrate records in batches
            batch_size = 100
            migrated_count = 0
            
            for i in range(0, record_count, batch_size):
                batch = sqlite_records[i:i + batch_size]
                
                for record in batch:
                    # Create new record for PostgreSQL
                    record_dict = {}
                    
                    # Get all column values
                    for column in model_class.__table__.columns:
                        value = getattr(record, column.name)
                        record_dict[column.name] = value
                    
                    # Create new record in PostgreSQL
                    new_record = model_class(**record_dict)
                    self.postgres_session.add(new_record)
                
                # Commit batch
                self.postgres_session.commit()
                migrated_count += len(batch)
                logger.info(f"Migrated {migrated_count}/{record_count} records for {table_name}")
            
            logger.info(f"Successfully migrated {migrated_count} records for table {table_name}")
            
        except Exception as e:
            logger.error(f"Error migrating table {table_name}: {e}")
            self.postgres_session.rollback()
            raise
    
    def _verify_migration(self):
        """Verify that migration was successful."""
        try:
            logger.info("Verifying migration")
            
            # Compare record counts
            tables_to_verify = [
                (User, "users"),
                (Manager, "managers"),
                (ProcessedFile, "processed_files"),
                (CallRecord, "call_records"),
                (ChecklistAnalysis, "checklist_analysis"),
                (AIAnalysis, "ai_analysis"),
                (LegacyQualityScore, "legacy_quality_scores")
            ]
            
            verification_results = []
            
            for model_class, table_name in tables_to_verify:
                sqlite_count = self.sqlite_session.query(model_class).count()
                postgres_count = self.postgres_session.query(model_class).count()
                
                match = sqlite_count == postgres_count
                verification_results.append({
                    'table': table_name,
                    'sqlite_count': sqlite_count,
                    'postgres_count': postgres_count,
                    'match': match
                })
                
                logger.info(f"Table {table_name}: SQLite={sqlite_count}, PostgreSQL={postgres_count}, Match={match}")
            
            # Check if all tables match
            all_match = all(result['match'] for result in verification_results)
            
            if all_match:
                logger.info("✅ Migration verification successful - all data migrated correctly")
                print("\n📊 Migration Verification Results:")
                for result in verification_results:
                    print(f"  {result['table']}: {result['sqlite_count']} records ✅")
            else:
                logger.error("❌ Migration verification failed - record counts don't match")
                print("\n❌ Migration Verification Results:")
                for result in verification_results:
                    status = "✅" if result['match'] else "❌"
                    print(f"  {result['table']}: SQLite={result['sqlite_count']}, PostgreSQL={result['postgres_count']} {status}")
                raise Exception("Migration verification failed")
            
        except Exception as e:
            logger.error(f"Error verifying migration: {e}")
            raise
    
    def _close_connections(self):
        """Close database connections."""
        try:
            if self.sqlite_session:
                self.sqlite_session.close()
            if self.postgres_session:
                self.postgres_session.close()
            if self.sqlite_engine:
                self.sqlite_engine.dispose()
            if self.postgres_engine:
                self.postgres_engine.dispose()
            logger.info("Closed all database connections")
        except Exception as e:
            logger.warning(f"Error closing connections: {e}")


def main():
    """Main migration function."""
    print("🚀 Starting SQLite to PostgreSQL Migration")
    print("="*50)
    
    # Configuration - using defaults for automation
    sqlite_url = "sqlite:///./voiceai_calls.db"
    postgres_url = "postgresql://postgres:password@localhost:5432"
    postgres_db_name = "voiceai_db"
    
    print(f"\n🔧 Migration Configuration:")
    print(f"  Source (SQLite): {sqlite_url}")
    print(f"  Target (PostgreSQL): {postgres_url}/{postgres_db_name}")
    print("")
    print("📋 Using default configuration for automated migration")
    
    try:
        # Execute migration
        migrator = PostgreSQLMigrator(sqlite_url, postgres_url, postgres_db_name)
        migrator.migrate()
        
        print("\n🎉 Migration completed successfully!")
        print(f"📝 Next steps:")
        print(f"  1. Update your .env file:")
        print(f"     DATABASE_URL={postgres_url}/{postgres_db_name}")
        print(f"  2. Install PostgreSQL driver: pip install psycopg2-binary")
        print(f"  3. Restart your application")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()