#!/usr/bin/env python3
"""
Enhanced Google Sheets Exporter with detailed checklist breakdown and color coding.
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


class EnhancedSheetsExporter:
    """Enhanced export with detailed checklist breakdown and color coding."""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.gc = None
        self.spreadsheet = None
        self._setup_google_sheets()
        
        # Define checklist criteria with descriptions
        self.checklist_criteria = {
            'greeting': {
                'name': 'ПРИВЕТСТВИЕ',
                'criteria': [
                    'Время до менеджера меньше 8 секунд',
                    'Корпоративное приветствие',
                    'Дружелюбный тон',
                    'Нет слов-паразитов "блин", "короче"',
                    'Озвучивает цель звонка',
                    'Не использует фразу "Вам удобно говорить?"',
                    'Не использует фразу "Могу ли я к Вам обратиться?"'
                ]
            },
            'contact': {
                'name': 'УСТАНОВЛЕНИЕ КОНТАКТА',
                'criteria': [
                    'Обращается по имени',
                    'Не перебивает клиента',
                    'Использует простой язык',
                    'Избегает формального тона',
                    'Общается на равных',
                    'Использует small talk',
                    'Делает комплимент',
                    'Использует юмор'
                ]
            },
            'programming': {
                'name': 'ПРОГРАММИРОВАНИЕ',
                'criteria': [
                    'Использует в начале разговора',
                    'Ведет диалог'
                ]
            },
            'need': {
                'name': 'ВЫЯВЛЕНИЕ ПОТРЕБНОСТИ',
                'criteria': [
                    'Задает обязательные вопросы',
                    'Выясняет сферу деятельности'
                ]
            },
            'presentation': {
                'name': 'ПРЕЗЕНТАЦИЯ ПРОДУКТА',
                'criteria': [
                    'Представляет компанию',
                    'Услуги с выгодами',
                    'Упоминает кейсы',
                    'Предлагает коммерческое предложение',
                    'Знает продукт'
                ]
            },
            'objections': {
                'name': 'ОБРАБОТКА ВОЗРАЖЕНИЙ',
                'criteria': [
                    'Обрабатывает возражения полностью',
                    'Соглашается и сопереживает',
                    'Аргументы соответствуют возражению',
                    'Не спорит с клиентом',
                    'Предлагает коммерческое предложение'
                ]
            },
            'closing': {
                'name': 'ЗАКРЫТИЕ СДЕЛКИ',
                'criteria': [
                    'Спрашивает остались ли вопросы',
                    'Уточняет куда отправить предложение',
                    'Спрашивает на какую дату услуга',
                    'Подводит итоги разговора',
                    'Озвучивает следующие шаги',
                    'Оставляет свои контакты'
                ]
            }
        }
    
    def _setup_google_sheets(self):
        """Initialize Google Sheets client."""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                config.google_service_account_file, 
                scope
            )
            self.gc = gspread.authorize(creds)
            self.spreadsheet = self.gc.open_by_key(config.google_spreadsheet_id)
            logger.info(f"Connected to Google Sheets: {self.spreadsheet.title}")
            
        except Exception as e:
            logger.error(f"Failed to setup Google Sheets: {e}")
            raise
    
    def export_all_manager_data(self):
        """Export all manager data with enhanced formatting."""
        try:
            logger.info("Starting enhanced export of all manager data to Google Sheets")
            
            managers = self.db_service.get_all_managers()
            logger.info(f"Found {len(managers)} managers to export")
            
            for manager in managers:
                self._export_enhanced_manager_sheet(manager)
            
            # Create summary sheet
            self._create_summary_sheet(managers)
            
            logger.info("Successfully exported all manager data to Google Sheets")
            
        except Exception as e:
            logger.error(f"Error exporting manager data: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _export_enhanced_manager_sheet(self, manager: Manager):
        """Export individual manager data with enhanced formatting."""
        try:
            sheet_name = f"Менеджер {manager.name}"
            logger.info(f"Exporting enhanced data for manager: {manager.name}")
            
            worksheet = self._get_or_create_worksheet(sheet_name)
            worksheet.clear()
            
            # Get manager's call records with analysis
            call_records = self._get_manager_call_records(manager.id)
            logger.info(f"Found {len(call_records)} call records for {manager.name}")
            
            # Prepare enhanced data for export
            self._write_enhanced_manager_data(worksheet, manager, call_records)
            
            # Apply formatting and colors
            self._apply_enhanced_formatting(worksheet, len(call_records))
            
            logger.info(f"Successfully exported enhanced data for {manager.name}")
                
        except Exception as e:
            logger.error(f"Error exporting manager {manager.name}: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _write_enhanced_manager_data(self, worksheet, manager: Manager, call_records: List[tuple]):
        """Write enhanced manager data with detailed breakdown."""
        row = 1
        
        # Manager info
        worksheet.update_cell(row, 1, f"МЕНЕДЖЕР: {manager.name}")
        row += 1
        worksheet.update_cell(row, 1, f"Email: {manager.email or 'Не указан'}")
        row += 1
        worksheet.update_cell(row, 1, f"Отдел: {manager.department or 'Не указан'}")
        row += 1
        worksheet.update_cell(row, 1, f"Статус: {manager.status}")
        row += 1
        worksheet.update_cell(row, 1, f"Дата создания отчета: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        row += 2
        
        # Process each call record
        for call_record, checklist_analysis, ai_analysis in call_records:
            row = self._write_call_analysis(worksheet, row, call_record, checklist_analysis, ai_analysis)
            row += 2  # Add spacing between calls
    
    def _write_call_analysis(self, worksheet, start_row: int, call_record: CallRecord, 
                           checklist_analysis: Optional[ChecklistAnalysis],
                           ai_analysis: Optional[AIAnalysis]) -> int:
        """Write detailed analysis for a single call."""
        row = start_row
        
        # Call header
        worksheet.update_cell(row, 1, f"ЗВОНОК: {call_record.file_name}")
        worksheet.update_cell(row, 1, f"ЗВОНОК: {call_record.file_name}")
        worksheet.format(f"A{row}", {
            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 1.0},
            "textFormat": {"bold": True, "fontSize": 12}
        })
        row += 1
        
        worksheet.update_cell(row, 1, f"Дата: {call_record.call_date.strftime('%Y-%m-%d %H:%M:%S') if call_record.call_date else 'Не указана'}")
        worksheet.update_cell(row, 3, f"Тип: {call_record.call_type or 'Не указан'}")
        row += 1
        
        # Detailed checklist analysis
        if checklist_analysis:
            row = self._write_detailed_checklist(worksheet, row, checklist_analysis)
        
        # AI analysis with explanations
        if ai_analysis:
            row = self._write_ai_analysis_with_explanations(worksheet, row, ai_analysis)
        
        return row
    
    def _write_detailed_checklist(self, worksheet, start_row: int, checklist: ChecklistAnalysis) -> int:
        """Write detailed checklist with color coding."""
        row = start_row
        
        # Checklist header
        worksheet.update_cell(row, 1, "ЧЕК-ЛИСТ АНАЛИЗ")
        worksheet.format(f"A{row}", {
            "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.2},
            "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })
        row += 1
        
        # Get individual scores for each criterion
        criterion_values = self._get_individual_criterion_scores(checklist)
        
        # Write each stage with detailed breakdown
        for stage_key, stage_info in self.checklist_criteria.items():
            # Stage header
            worksheet.update_cell(row, 1, stage_info['name'])
            stage_total = getattr(checklist, f"{stage_key}_total")
            max_score = len(stage_info['criteria'])
            percentage = (float(stage_total) / max_score) * 100 if max_score > 0 else 0
            
            worksheet.update_cell(row, 2, f"{float(stage_total):.1f}/{max_score}")
            worksheet.update_cell(row, 3, f"{percentage:.1f}%")
            
            # Color code the stage total
            color = self._get_color_for_percentage(percentage)
            worksheet.format(f"B{row}:C{row}", {"backgroundColor": color})
            row += 1
            
            # Write individual criteria
            stage_values = criterion_values.get(stage_key, [])
            for i, criterion_name in enumerate(stage_info['criteria']):
                score = stage_values[i] if i < len(stage_values) else 0
                
                worksheet.update_cell(row, 2, criterion_name)
                worksheet.update_cell(row, 3, f"{float(score):.1f}")
                
                # Color code individual criterion
                criterion_color = self._get_color_for_score(float(score))
                worksheet.format(f"C{row}", {"backgroundColor": criterion_color})
                row += 1
            
            row += 1  # Spacing between stages
        
        return row
    
    def _write_ai_analysis_with_explanations(self, worksheet, start_row: int, ai_analysis: AIAnalysis) -> int:
        """Write AI analysis with detailed explanations."""
        row = start_row
        
        # AI Analysis header
        worksheet.update_cell(row, 1, "AI АНАЛИЗ")
        worksheet.format(f"A{row}", {
            "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.6},
            "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })
        row += 1
        
        # AI categories with scores and explanations
        ai_categories = [
            ("Установление контакта", ai_analysis.contact_establishment_value, ai_analysis.contact_establishment_explanation),
            ("Квалификация", ai_analysis.qualification_value, ai_analysis.qualification_explanation),
            ("Выявление потребности", ai_analysis.needs_identification_value, ai_analysis.needs_identification_explanation),
            ("Презентация продукта", ai_analysis.product_presentation_value, ai_analysis.product_presentation_explanation),
            ("Обработка возражений", ai_analysis.objection_handling_value, ai_analysis.objection_handling_explanation),
            ("Закрытие сделки", ai_analysis.closing_value, ai_analysis.closing_explanation),
            ("Вероятность продажи", ai_analysis.sale_probability_value, ai_analysis.sale_probability_explanation)
        ]
        
        for category_name, score, explanation in ai_categories:
            if score is not None:
                worksheet.update_cell(row, 1, category_name)
                worksheet.update_cell(row, 2, f"{float(score):.1f}%")
                
                # Color code AI score
                color = self._get_color_for_percentage(float(score))
                worksheet.format(f"B{row}", {"backgroundColor": color})
                
                # Add explanation if available
                if explanation:
                    worksheet.update_cell(row, 3, explanation)
                row += 1
        
        # Additional AI data
        if ai_analysis.summary:
            worksheet.update_cell(row, 1, "Краткое резюме:")
            worksheet.update_cell(row, 2, ai_analysis.summary)
            row += 1
        
        if ai_analysis.client_name:
            worksheet.update_cell(row, 1, "Имя клиента:")
            worksheet.update_cell(row, 2, ai_analysis.client_name)
            row += 1
        
        if ai_analysis.manager_responsible:
            worksheet.update_cell(row, 1, "Ответственный менеджер:")
            worksheet.update_cell(row, 2, ai_analysis.manager_responsible)
            row += 1
        
        return row
    
    def _get_individual_criterion_scores(self, checklist: ChecklistAnalysis) -> Dict[str, List[float]]:
        """Extract individual criterion scores from checklist analysis."""
        return {
            'greeting': [
                float(checklist.greeting_time_before_manager or 0),
                float(checklist.greeting_corporate_greeting or 0),
                float(checklist.greeting_tone_friendly or 0),
                float(checklist.greeting_no_rush_words or 0),
                float(checklist.greeting_states_purpose or 0),
                float(checklist.greeting_no_convenient_phrase or 0),
                float(checklist.greeting_no_address_phrase or 0)
            ],
            'contact': [
                float(checklist.contact_addresses_by_name or 0),
                float(checklist.contact_no_interrupt or 0),
                float(checklist.contact_simple_language or 0),
                float(checklist.contact_avoids_formal_tone or 0),
                float(checklist.contact_communicates_equal or 0),
                float(checklist.contact_uses_small_talk or 0),
                float(checklist.contact_gives_compliment or 0),
                float(checklist.contact_uses_humor or 0)
            ],
            'programming': [
                float(checklist.programming_uses_at_start or 0),
                float(checklist.programming_leads_conversation or 0)
            ],
            'need': [
                float(checklist.need_asks_required_questions or 0),
                float(checklist.need_finds_business_area or 0)
            ],
            'presentation': [
                float(checklist.presentation_presents_company or 0),
                float(checklist.presentation_services_with_benefits or 0),
                float(checklist.presentation_mentions_cases or 0),
                float(checklist.presentation_offers_proposal or 0),
                float(checklist.presentation_knows_product or 0)
            ],
            'objections': [
                float(checklist.objections_handles_fully or 0),
                float(checklist.objections_agrees_empathizes or 0),
                float(checklist.objections_arguments_match or 0),
                float(checklist.objections_no_argue or 0),
                float(checklist.objections_offers_proposal or 0)
            ],
            'closing': [
                float(checklist.closing_asks_questions_remain or 0),
                float(checklist.closing_clarifies_proposal_send or 0),
                float(checklist.closing_asks_service_date or 0),
                float(checklist.closing_summarizes_conversation or 0),
                float(checklist.closing_states_next_steps or 0),
                float(checklist.closing_leaves_contacts or 0)
            ]
        }
    
    def _get_color_for_score(self, score: float) -> Dict[str, float]:
        """Get color based on score (0, 0.5, 1)."""
        if score >= 1.0:
            return {"red": 0.2, "green": 0.8, "blue": 0.2}  # Green
        elif score >= 0.5:
            return {"red": 1.0, "green": 1.0, "blue": 0.2}  # Yellow
        else:
            return {"red": 1.0, "green": 0.2, "blue": 0.2}  # Red
    
    def _get_color_for_percentage(self, percentage: float) -> Dict[str, float]:
        """Get color based on percentage."""
        if percentage >= 80:
            return {"red": 0.2, "green": 0.8, "blue": 0.2}  # Green
        elif percentage >= 60:
            return {"red": 1.0, "green": 1.0, "blue": 0.2}  # Yellow
        else:
            return {"red": 1.0, "green": 0.2, "blue": 0.2}  # Red
    
    def _get_or_create_worksheet(self, sheet_name: str):
        """Get existing worksheet or create new one."""
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            logger.info(f"Found existing worksheet: {sheet_name}")
            return worksheet
        except WorksheetNotFound:
            logger.info(f"Creating new worksheet: {sheet_name}")
            worksheet = self.spreadsheet.add_worksheet(
                title=sheet_name,
                rows=1000,
                cols=20
            )
            return worksheet
    
    def _get_manager_call_records(self, manager_id: int) -> List[tuple]:
        """Get all call records with analysis for a manager."""
        session = self.db_service.get_session()
        try:
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
    
    def _apply_enhanced_formatting(self, worksheet, num_calls: int):
        """Apply enhanced formatting to the worksheet."""
        try:
            # Set column widths
            worksheet.columns_auto_resize(0, 3)
            
            # Freeze first row
            worksheet.freeze(rows=1)
            
        except Exception as e:
            logger.warning(f"Could not apply enhanced formatting: {e}")
    
    def _create_summary_sheet(self, managers: List[Manager]):
        """Create summary sheet with overall statistics."""
        try:
            sheet_name = "Общая сводка"
            logger.info("Creating summary sheet")
            
            worksheet = self._get_or_create_worksheet(sheet_name)
            worksheet.clear()
            
            row = 1
            worksheet.update_cell(row, 1, "Общая сводка по менеджерам")
            worksheet.format(f"A{row}", {
                "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.8},
                "textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
            })
            row += 1
            
            worksheet.update_cell(row, 1, f"Дата создания: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
            row += 2
            
            # Headers
            headers = ["Менеджер", "Email", "Отдел", "Статус", "Всего звонков", "Средний балл ЧЛ", "Средний балл AI"]
            for col, header in enumerate(headers, 1):
                worksheet.update_cell(row, col, header)
            
            worksheet.format(f"A{row}:{chr(64+len(headers))}{row}", {
                "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8},
                "textFormat": {"bold": True}
            })
            row += 1
            
            # Manager data
            for manager in managers:
                stats = self.db_service.get_manager_statistics(manager.name, 365)
                
                data = [
                    manager.name,
                    manager.email or "",
                    manager.department or "",
                    manager.status,
                    stats.get('total_calls', 0),
                    f"{stats.get('avg_checklist_score', 0):.1f}",
                    f"{stats.get('avg_ai_score', 0):.1f}"
                ]
                
                for col, value in enumerate(data, 1):
                    worksheet.update_cell(row, col, value)
                row += 1
            
            logger.info("Successfully created summary sheet")
                
        except Exception as e:
            logger.error(f"Error creating summary sheet: {e}")


def main():
    """Main function for enhanced export."""
    exporter = EnhancedSheetsExporter()
    exporter.export_all_manager_data()


if __name__ == "__main__":
    main()