#!/usr/bin/env python3
"""
Script to export enhanced data to Google Sheets with detailed checklist and color coding.
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from enhanced_sheets_exporter import EnhancedSheetsExporter
from loguru import logger

async def main():
    """Export enhanced manager data to Google Sheets."""
    try:
        logger.info("Starting enhanced Google Sheets export script")
        
        # Create enhanced exporter and run export
        exporter = EnhancedSheetsExporter()
        exporter.export_all_manager_data()
        
        logger.info("Enhanced export completed successfully!")
        print("✅ Улучшенные данные экспортированы в Google Sheets!")
        print("📊 Каждый лист содержит:")
        print("  🔍 Детальный чек-лист по всем 33 критериям")
        print("  🎨 Цветовую раскраску: 0=красный, 0.5=желтый, 1=зеленый")
        print("  🤖 AI анализ с объяснениями по каждому критерию")
        print("  📋 Подробную разбивку по стадиям продаж")
        
    except Exception as e:
        logger.error(f"Enhanced export failed: {e}")
        print(f"❌ Экспорт не удался: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())