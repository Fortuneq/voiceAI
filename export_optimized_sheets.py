#!/usr/bin/env python3
"""
Script to export optimized data to Google Sheets with batch operations.
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from optimized_sheets_exporter import OptimizedSheetsExporter
from loguru import logger

async def main():
    """Export optimized manager data to Google Sheets."""
    try:
        logger.info("Starting optimized Google Sheets export script")
        
        print("🚀 Запуск оптимизированного экспорта в Google Sheets...")
        print("⏱️  Используем batch операции для избежания лимитов API")
        print("📋 Экспортируем детальный чек-лист с разбивкой по всем 33 критериям")
        print("🤖 Добавляем AI анализ с объяснениями")
        print("")
        
        # Create optimized exporter and run export
        exporter = OptimizedSheetsExporter()
        exporter.export_all_manager_data()
        
        logger.info("Optimized export completed successfully!")
        print("✅ Оптимизированные данные экспортированы в Google Sheets!")
        print("📊 Каждый лист содержит:")
        print("  🔍 Полный чек-лист по всем 33 критериям")
        print("  📈 Подробную разбивку по стадиям продаж")
        print("  🤖 AI анализ с объяснениями по каждому критерию")
        print("  📋 Информацию о менеджере и звонках")
        print("")
        print("💡 Примечание: Цветовая раскраска будет добавлена в следующей версии")
        print("   для избежания превышения лимитов Google Sheets API")
        
    except Exception as e:
        logger.error(f"Optimized export failed: {e}")
        print(f"❌ Экспорт не удался: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())