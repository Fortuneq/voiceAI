#!/usr/bin/env python3
"""
Google Sheets Exporter for VoiceAI Call Analysis System.

Exports all database data to Google Sheets with individual manager sheets.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import traceback

from loguru import logger
import gspread
from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound
from oauth2client.service_account import ServiceAccountCredentials

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from database_service import DatabaseService
from database_models import Manager, CallRecord, ChecklistAnalysis, AIAnalysis
from config import config


class SheetsExporter:
    """Export database data to Google Sheets with individual manager sheets."""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.gc = None
        self.spreadsheet = None
        self._setup_google_sheets()
    
    def _setup_google_sheets(self):
        """Initialize Google Sheets client."""
        try:
            # Setup Google Sheets API credentials
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                config.google_service_account_file, 
                scope
            )
            self.gc = gspread.authorize(creds)
            
            # Open the spreadsheet
            self.spreadsheet = self.gc.open_by_key(config.google_spreadsheet_id)
            logger.info(f"Connected to Google Sheets: {self.spreadsheet.title}")
            
        except Exception as e:
            logger.error(f"Failed to setup Google Sheets: {e}")
            raise
    
    def export_all_manager_data(self):
        """Export all manager data to Google Sheets with individual sheets."""
        try:
            logger.info("Starting export of all manager data to Google Sheets")
            
            # Get all managers from database
            managers = self.db_service.get_all_managers()
            logger.info(f"Found {len(managers)} managers to export")
            
            for manager in managers:
                self._export_manager_sheet(manager)
            
            # Create summary sheet
            self._create_summary_sheet(managers)
            
            logger.info("Successfully exported all manager data to Google Sheets")
            
        except Exception as e:
            logger.error(f"Error exporting manager data: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _export_manager_sheet(self, manager: Manager):
        """Export individual manager data to their own sheet."""
        try:
            sheet_name = f"Менеджер {manager.name}"
            logger.info(f"Exporting data for manager: {manager.name}")
            
            # Get or create worksheet
            worksheet = self._get_or_create_worksheet(sheet_name)
            
            # Clear existing data
            worksheet.clear()
            
            # Get manager's call records with analysis
            call_records = self._get_manager_call_records(manager.id)
            logger.info(f"Found {len(call_records)} call records for {manager.name}")
            
            # Prepare data for export
            data = self._prepare_manager_data(manager, call_records)
            
            # Write data to sheet
            if data:
                worksheet.update(data, value_input_option='USER_ENTERED')
                logger.info(f"Successfully exported {len(data)} rows for {manager.name}")
            else:
                # Write header even if no data
                headers = self._get_manager_sheet_headers()
                worksheet.update([headers], value_input_option='USER_ENTERED')
                logger.info(f"No call data found for {manager.name}, added headers only")
                
        except Exception as e:
            logger.error(f"Error exporting manager {manager.name}: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _get_or_create_worksheet(self, sheet_name: str):
        """Get existing worksheet or create new one."""
        try:
            # Try to get existing worksheet
            worksheet = self.spreadsheet.worksheet(sheet_name)
            logger.info(f"Found existing worksheet: {sheet_name}")
            return worksheet
        except WorksheetNotFound:
            # Create new worksheet
            logger.info(f"Creating new worksheet: {sheet_name}")
            worksheet = self.spreadsheet.add_worksheet(
                title=sheet_name,
                rows=1000,
                cols=50
            )
            return worksheet
    
    def _get_manager_call_records(self, manager_id: int) -> List[tuple]:
        """Get all call records with analysis for a manager."""
        session = self.db_service.get_session()
        try:
            # Query call records with associated analysis
            results = session.query(
                CallRecord, 
                ChecklistAnalysis, 
                AIAnalysis
            ).outerjoin(
                ChecklistAnalysis, CallRecord.id == ChecklistAnalysis.call_record_id
            ).outerjoin(
                AIAnalysis, CallRecord.id == AIAnalysis.call_record_id
            ).filter(
                CallRecord.manager_id == manager_id
            ).order_by(
                CallRecord.call_date.desc()
            ).all()
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting call records for manager {manager_id}: {e}")
            return []
        finally:
            session.close()
    
    def _prepare_manager_data(self, manager: Manager, call_records: List[tuple]) -> List[List[str]]:
        """Prepare manager data for Google Sheets export."""
        data = []
        
        # Add manager info header (remove VoiceAI header)
        data.append([f"МЕНЕДЖЕР: {manager.name}"])
        data.append([f"Email: {manager.email or 'Не указан'}"])
        data.append([f"Отдел: {manager.department or 'Не указан'}"])
        data.append([f"Статус: {manager.status}"])
        data.append([f"Дата создания отчета: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"])
        data.append([])  # Empty row
        
        # Add column headers for call data
        call_headers = [
            "Дата звонка", "Тип звонка", "Название файла", "Статус обработки",
            
            # Checklist Analysis Headers
            "=== ЧЕК-ЛИСТ АНАЛИЗ ===", "", "", "",
            "Приветствие (балл)", "Приветствие (%)", 
            "Контакт (балл)", "Контакт (%)",
            "Программирование (балл)", "Программирование (%)",
            "Потребность (балл)", "Потребность (%)",
            "Презентация (балл)", "Презентация (%)",
            "Возражения (балл)", "Возражения (%)",
            "Закрытие (балл)", "Закрытие (%)",
            "Общий балл ЧЛ", "Общий % ЧЛ",
            
            # AI Analysis Headers
            "=== AI АНАЛИЗ ===", "", "", "",
            "Установление контакта (%)", "Квалификация (%)",
            "Выявление потребности (%)", "Презентация продукта (%)",
            "Обработка возражений (%)", "Закрытие сделки (%)",
            "Вероятность продажи (%)", "Средний AI балл (%)",
            "Краткое резюме", "Имя клиента", "Ответственность менеджера"
        ]
        data.append(call_headers)
        
        # Add call data
        for call_record, checklist_analysis, ai_analysis in call_records:
            row = self._format_call_record_row(call_record, checklist_analysis, ai_analysis)
            data.append(row)
        
        return data
    
    def _get_manager_sheet_headers(self) -> List[str]:
        """Get headers for manager sheet."""
        return [
            "VoiceAI Call Analysis Report",
            "Сгенерирован:",
            datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        ]
    
    def _format_call_record_row(self, call_record: CallRecord, 
                               checklist_analysis: Optional[ChecklistAnalysis],
                               ai_analysis: Optional[AIAnalysis]) -> List[str]:
        """Format a single call record row for export."""
        
        # Basic call info
        row = [
            call_record.call_date.strftime('%Y-%m-%d %H:%M:%S') if call_record.call_date else '',
            call_record.call_type or '',
            call_record.file_name or '',
            call_record.processing_status or ''
        ]
        
        # Checklist analysis data
        if checklist_analysis:
            # Calculate max scores for percentage calculation
            max_scores = {
                'greeting': 7.0, 'contact': 8.0, 'programming': 2.0, 'need': 2.0,
                'presentation': 5.0, 'objections': 5.0, 'closing': 6.0
            }
            
            greeting_total = float(checklist_analysis.greeting_total)
            contact_total = float(checklist_analysis.contact_total)
            programming_total = float(checklist_analysis.programming_total)
            need_total = float(checklist_analysis.need_total)
            presentation_total = float(checklist_analysis.presentation_total)
            objections_total = float(checklist_analysis.objections_total)
            closing_total = float(checklist_analysis.closing_total)
            overall_total = float(checklist_analysis.overall_total)
            overall_max = sum(max_scores.values())
            
            row.extend([
                "", "", "", "",  # Spacers for checklist section
                f"{greeting_total:.1f}",
                f"{(greeting_total / max_scores['greeting'] * 100):.1f}%" if greeting_total > 0 else "0%",
                f"{contact_total:.1f}",
                f"{(contact_total / max_scores['contact'] * 100):.1f}%" if contact_total > 0 else "0%",
                f"{programming_total:.1f}",
                f"{(programming_total / max_scores['programming'] * 100):.1f}%" if programming_total > 0 else "0%",
                f"{need_total:.1f}",
                f"{(need_total / max_scores['need'] * 100):.1f}%" if need_total > 0 else "0%",
                f"{presentation_total:.1f}",
                f"{(presentation_total / max_scores['presentation'] * 100):.1f}%" if presentation_total > 0 else "0%",
                f"{objections_total:.1f}",
                f"{(objections_total / max_scores['objections'] * 100):.1f}%" if objections_total > 0 else "0%",
                f"{closing_total:.1f}",
                f"{(closing_total / max_scores['closing'] * 100):.1f}%" if closing_total > 0 else "0%",
                f"{overall_total:.1f}",
                f"{(overall_total / overall_max * 100):.1f}%" if overall_total > 0 else "0%"
            ])
        else:
            # Empty checklist data
            row.extend([""] * 20)
        
        # AI analysis data
        if ai_analysis:
            avg_score = ai_analysis.average_score if ai_analysis.average_score else 0
            
            row.extend([
                "", "", "", "",  # Spacers for AI section
                f"{ai_analysis.contact_establishment_value:.1f}%" if ai_analysis.contact_establishment_value else "",
                f"{ai_analysis.qualification_value:.1f}%" if ai_analysis.qualification_value else "",
                f"{ai_analysis.needs_identification_value:.1f}%" if ai_analysis.needs_identification_value else "",
                f"{ai_analysis.product_presentation_value:.1f}%" if ai_analysis.product_presentation_value else "",
                f"{ai_analysis.objection_handling_value:.1f}%" if ai_analysis.objection_handling_value else "",
                f"{ai_analysis.closing_value:.1f}%" if ai_analysis.closing_value else "",
                f"{ai_analysis.sale_probability_value:.1f}%" if ai_analysis.sale_probability_value else "",
                f"{avg_score:.1f}%" if avg_score > 0 else "",
                ai_analysis.summary or "",
                ai_analysis.client_name or "",
                ai_analysis.manager_responsible or ""
            ])
        else:
            # Empty AI data
            row.extend([""] * 15)
        
        return row
    
    def _create_summary_sheet(self, managers: List[Manager]):
        """Create summary sheet with overall statistics."""
        try:
            sheet_name = "Общая сводка"
            logger.info("Creating summary sheet")
            
            worksheet = self._get_or_create_worksheet(sheet_name)
            worksheet.clear()
            
            # Prepare summary data
            summary_data = self._prepare_summary_data(managers)
            
            if summary_data:
                worksheet.update(summary_data, value_input_option='USER_ENTERED')
                logger.info("Successfully created summary sheet")
                
        except Exception as e:
            logger.error(f"Error creating summary sheet: {e}")
            logger.error(traceback.format_exc())
    
    def _prepare_summary_data(self, managers: List[Manager]) -> List[List[str]]:
        """Prepare summary data for all managers."""
        data = []
        
        # Headers
        data.append(["VoiceAI Call Analysis - Общая сводка по менеджерам"])
        data.append([f"Дата создания: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"])
        data.append([])
        
        # Column headers
        headers = [
            "Менеджер", "Email", "Отдел", "Статус",
            "Всего звонков", "Входящих", "Исходящих",
            "Средний балл ЧЛ", "Средний балл AI",
            "Последний звонок"
        ]
        data.append(headers)
        
        # Manager statistics
        for manager in managers:
            stats = self.db_service.get_manager_statistics(manager.name, 365)  # Last year
            
            row = [
                manager.name,
                manager.email or "",
                manager.department or "",
                manager.status,
                stats.get('total_calls', 0),
                stats.get('inbound_calls', 0),
                stats.get('outbound_calls', 0),
                f"{stats.get('avg_checklist_score', 0):.1f}",
                f"{stats.get('avg_ai_score', 0):.1f}",
                stats.get('last_call_date', '').strftime('%Y-%m-%d') if stats.get('last_call_date') else ""
            ]
            data.append(row)
        
        return data
    
    def export_single_manager(self, manager_name: str):
        """Export data for a single manager."""
        try:
            session = self.db_service.get_session()
            manager = session.query(Manager).filter(Manager.name == manager_name).first()
            session.close()
            
            if not manager:
                logger.error(f"Manager {manager_name} not found")
                return
            
            self._export_manager_sheet(manager)
            logger.info(f"Successfully exported data for manager: {manager_name}")
            
        except Exception as e:
            logger.error(f"Error exporting single manager {manager_name}: {e}")
            raise


def main():
    """Main function for command line usage."""
    if len(sys.argv) > 1:
        manager_name = sys.argv[1]
        exporter = SheetsExporter()
        exporter.export_single_manager(manager_name)
    else:
        exporter = SheetsExporter()
        exporter.export_all_manager_data()


if __name__ == "__main__":
    main()