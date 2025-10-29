#!/usr/bin/env python3
"""
Optimized Google Sheets Exporter with batch operations to avoid API limits.
"""

import sys
import time
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


class OptimizedSheetsExporter:
    """Optimized export with batch operations to avoid API limits."""
    
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
        """Export all manager data with optimized batch operations."""
        try:
            logger.info("Starting optimized export of all manager data to Google Sheets")
            
            managers = self.db_service.get_all_managers()
            logger.info(f"Found {len(managers)} managers to export")
            
            for i, manager in enumerate(managers):
                logger.info(f"Processing manager {i+1}/{len(managers)}: {manager.name}")
                self._export_optimized_manager_sheet(manager)
                
                # Add delay between managers to avoid API limits
                if i < len(managers) - 1:
                    logger.info("Waiting 30 seconds to avoid API limits...")
                    time.sleep(30)
            
            # Create summary sheet
            self._create_summary_sheet(managers)
            
            logger.info("Successfully exported all manager data to Google Sheets")
            
        except Exception as e:
            logger.error(f"Error exporting manager data: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _export_optimized_manager_sheet(self, manager: Manager):
        """Export individual manager data with batch operations."""
        try:
            sheet_name = f"Менеджер {manager.name}"
            logger.info(f"Exporting optimized data for manager: {manager.name}")
            
            worksheet = self._get_or_create_worksheet(sheet_name)
            worksheet.clear()
            
            # Get manager's call records with analysis
            call_records = self._get_manager_call_records(manager.id)
            logger.info(f"Found {len(call_records)} call records for {manager.name}")
            
            # Prepare all data as one big batch
            all_data = self._prepare_optimized_manager_data(manager, call_records)
            
            # Write all data in one batch operation
            if all_data:
                worksheet.update(all_data, value_input_option='USER_ENTERED')
                logger.info(f"Successfully wrote {len(all_data)} rows for {manager.name}")
                
                # Apply formatting in batch
                self._apply_optimized_formatting(worksheet, len(all_data))
            
            logger.info(f"Successfully exported optimized data for {manager.name}")
                
        except Exception as e:
            logger.error(f"Error exporting manager {manager.name}: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _prepare_optimized_manager_data(self, manager: Manager, call_records: List[tuple]) -> List[List[str]]:
        """Prepare all manager data as a single batch."""
        data = []
        
        # Manager info header
        data.append([f"МЕНЕДЖЕР: {manager.name}"])
        data.append([f"Email: {manager.email or 'Не указан'}"])
        data.append([f"Отдел: {manager.department or 'Не указан'}"])
        data.append([f"Статус: {manager.status}"])
        data.append([f"Дата создания отчета: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"])
        data.append([])  # Empty row
        
        # Process each call record
        for call_record, checklist_analysis, ai_analysis in call_records:
            data.extend(self._format_call_analysis_batch(call_record, checklist_analysis, ai_analysis))
            data.append([])  # Add spacing between calls
        
        return data
    
    def _format_call_analysis_batch(self, call_record: CallRecord, 
                                  checklist_analysis: Optional[ChecklistAnalysis],
                                  ai_analysis: Optional[AIAnalysis]) -> List[List[str]]:
        """Format detailed analysis for a single call as batch data."""
        data = []
        
        # Call header
        data.append([f"ЗВОНОК: {call_record.file_name}"])
        data.append([
            f"Дата: {call_record.call_date.strftime('%Y-%m-%d %H:%M:%S') if call_record.call_date else 'Не указана'}",
            "",
            f"Тип: {call_record.call_type or 'Не указан'}"
        ])
        data.append([])
        
        # Detailed checklist analysis
        if checklist_analysis:
            data.extend(self._format_detailed_checklist_batch(checklist_analysis))
        
        # AI analysis with explanations
        if ai_analysis:
            data.extend(self._format_ai_analysis_batch(ai_analysis))
        
        return data
    
    def _format_detailed_checklist_batch(self, checklist: ChecklistAnalysis) -> List[List[str]]:
        """Format detailed checklist as batch data."""
        data = []
        
        # Checklist header
        data.append(["ЧЕК-ЛИСТ АНАЛИЗ"])
        data.append([])
        
        # Get individual scores for each criterion
        criterion_values = self._get_individual_criterion_scores(checklist)
        
        # Format each stage with detailed breakdown
        for stage_key, stage_info in self.checklist_criteria.items():
            # Stage header
            stage_total = getattr(checklist, f"{stage_key}_total")
            max_score = len(stage_info['criteria'])
            percentage = (float(stage_total) / max_score) * 100 if max_score > 0 else 0
            
            data.append([
                stage_info['name'],
                f"{float(stage_total):.1f}/{max_score}",
                f"{percentage:.1f}%"
            ])
            
            # Individual criteria
            stage_values = criterion_values.get(stage_key, [])
            for i, criterion_name in enumerate(stage_info['criteria']):
                score = stage_values[i] if i < len(stage_values) else 0
                
                data.append([
                    "",
                    criterion_name,
                    f"{float(score):.1f}"
                ])
            
            data.append([])  # Spacing between stages
        
        return data
    
    def _format_ai_analysis_batch(self, ai_analysis: AIAnalysis) -> List[List[str]]:
        """Format AI analysis as batch data."""
        data = []
        
        # AI Analysis header
        data.append(["AI АНАЛИЗ"])
        data.append([])
        
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
                data.append([
                    category_name,
                    f"{float(score):.1f}%",
                    explanation or ""
                ])
        
        # Additional AI data
        data.append([])
        if ai_analysis.summary:
            data.append(["Краткое резюме:", ai_analysis.summary])
        
        if ai_analysis.client_name:
            data.append(["Имя клиента:", ai_analysis.client_name])
        
        if ai_analysis.manager_responsible:
            data.append(["Ответственный менеджер:", ai_analysis.manager_responsible])
        
        return data
    
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
    
    def _apply_optimized_formatting(self, worksheet, num_rows: int):
        """Apply basic formatting optimized for batch operations."""
        try:
            # Apply basic formatting in batches
            logger.info(f"Applying formatting to {num_rows} rows")
            
            # Set column widths - single batch operation
            worksheet.columns_auto_resize(0, 3)
            
            # Note: Color formatting would require too many API calls
            # We'll focus on data content instead of colors for now
            
        except Exception as e:
            logger.warning(f"Could not apply formatting: {e}")
    
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
                rows=2000,
                cols=10
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
    
    def _create_summary_sheet(self, managers: List[Manager]):
        """Create summary sheet with overall statistics."""
        try:
            sheet_name = "Общая сводка"
            logger.info("Creating summary sheet")
            
            worksheet = self._get_or_create_worksheet(sheet_name)
            worksheet.clear()
            
            # Prepare summary data
            summary_data = []
            
            summary_data.append(["Общая сводка по менеджерам"])
            summary_data.append([f"Дата создания: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"])
            summary_data.append([])
            
            # Headers
            headers = ["Менеджер", "Email", "Отдел", "Статус", "Всего звонков", "Средний балл ЧЛ", "Средний балл AI"]
            summary_data.append(headers)
            
            # Manager data
            for manager in managers:
                stats = self.db_service.get_manager_statistics(manager.name, 365)
                
                row = [
                    manager.name,
                    manager.email or "",
                    manager.department or "",
                    manager.status,
                    stats.get('total_calls', 0),
                    f"{stats.get('avg_checklist_score', 0):.1f}",
                    f"{stats.get('avg_ai_score', 0):.1f}"
                ]
                summary_data.append(row)
            
            # Write all data in one batch
            worksheet.update(summary_data, value_input_option='USER_ENTERED')
            
            logger.info("Successfully created summary sheet")
                
        except Exception as e:
            logger.error(f"Error creating summary sheet: {e}")


def main():
    """Main function for optimized export."""
    exporter = OptimizedSheetsExporter()
    exporter.export_all_manager_data()


if __name__ == "__main__":
    main()