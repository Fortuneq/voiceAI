#!/usr/bin/env python3
"""
Script to export data to Google Sheets with smart color coding using emojis.
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from smart_colored_exporter import SmartColoredExporter
from loguru import logger

async def main():
    """Export manager data to Google Sheets with smart color coding."""
    try:
        logger.info("Starting smart colored Google Sheets export script")
        
        print("🧠 Запуск УМНОЙ цветовой раскраски в Google Sheets...")
        print("🎯 Используем EMOJI индикаторы вместо фоновых цветов:")
        print("  🔴 0 баллов = КРАСНЫЙ КРУГ")
        print("  🟡 0.5 баллов = ЖЕЛТЫЙ КРУГ") 
        print("  🟢 1 балл = ЗЕЛЕНЫЙ КРУГ")
        print("📊 Процентные показатели:")
        print("  🔴 <60% = КРАСНЫЙ")
        print("  🟡 60-79% = ЖЕЛТЫЙ") 
        print("  🟢 80%+ = ЗЕЛЕНЫЙ")
        print("⚡ ПРЕИМУЩЕСТВА:")
        print("  • Не превышаем лимиты Google Sheets API")
        print("  • Визуально понятные индикаторы")
        print("  • Быстрая обработка")
        print("  • Минимальное форматирование только заголовков")
        print("")
        
        # Create smart colored exporter and run export
        exporter = SmartColoredExporter()
        exporter.export_all_manager_data()
        
        logger.info("Smart colored export completed successfully!")
        print("✅ УМНАЯ цветовая раскраска завершена!")
        print("🎯 Каждый лист содержит:")
        print("  🎨 EMOJI индикаторы для всех оценок:")
        print("     • 🟢 - Отличное выполнение критерия")
        print("     • 🟡 - Частичное выполнение")
        print("     • 🔴 - Не выполнено, требует внимания")
        print("  🔍 Полный чек-лист по всем 33 критериям")
        print("  🤖 AI анализ с индикаторами и объяснениями")
        print("  📈 Визуальные индикаторы по стадиям продаж")
        print("  📋 Информацию о менеджере и звонках")
        print("")
        print("🎉 Теперь сразу видно что нужно улучшить!")
        print("💡 Красные кружки = приоритеты для работы с менеджером")
        
    except Exception as e:
        logger.error(f"Smart colored export failed: {e}")
        print(f"❌ Умный экспорт не удался: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())