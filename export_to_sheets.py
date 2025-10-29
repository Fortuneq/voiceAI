#!/usr/bin/env python3
"""
Script to export all database data to Google Sheets.
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from sheets_exporter import SheetsExporter
from loguru import logger

async def main():
    """Export all manager data to Google Sheets."""
    try:
        logger.info("Starting Google Sheets export script")
        
        # Create exporter and run export
        exporter = SheetsExporter()
        exporter.export_all_manager_data()
        
        logger.info("Export completed successfully!")
        print("✅ All data has been exported to Google Sheets!")
        print("📊 Check your spreadsheet for individual manager sheets and summary.")
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        print(f"❌ Export failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())