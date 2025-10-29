#!/usr/bin/env python3
"""
Script to export data to Google Sheets with full color coding.
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from colored_sheets_exporter import ColoredSheetsExporter
from loguru import logger

async def main():
    """Export manager data to Google Sheets with color coding."""
    try:
        logger.info("Starting colored Google Sheets export script")
        
        print("🎨 Запуск цветового экспорта в Google Sheets...")
        print("🔴 0 баллов = КРАСНЫЙ")
        print("🟡 0.5 баллов = ЖЕЛТЫЙ") 
        print("🟢 1 балл = ЗЕЛЕНЫЙ")
        print("📊 Процентные показатели: <60% = красный, 60-79% = желтый, 80%+ = зеленый")
        print("⏱️  Используем оптимизированные batch операции")
        print("")
        
        # Create colored exporter and run export
        exporter = ColoredSheetsExporter()
        exporter.export_all_manager_data()
        
        logger.info("Colored export completed successfully!")
        print("✅ Цветовые данные экспортированы в Google Sheets!")
        print("🎯 Каждый лист содержит:")
        print("  🎨 Полную цветовую раскраску по схеме:")
        print("     • 0 = 🔴 Красный (не выполнено)")
        print("     • 0.5 = 🟡 Желтый (частично выполнено)")
        print("     • 1 = 🟢 Зеленый (полностью выполнено)")
        print("  🔍 Детальный чек-лист по всем 33 критериям")
        print("  🤖 AI анализ с цветовой индикацией и объяснениями")
        print("  📈 Цветовые заголовки для лучшей навигации")
        print("")
        print("🎉 Теперь легко видеть где нужны улучшения!")
        
    except Exception as e:
        logger.error(f"Colored export failed: {e}")
        print(f"❌ Цветовой экспорт не удался: {e}")
        print("💡 Возможно превышен лимит API - попробуйте позже или используйте обычный экспорт")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())