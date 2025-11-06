#!/usr/bin/env python3
"""
Smart Google Sheets Exporter with selective color coding for key elements only.
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
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


class SmartColoredExporter:
    """Smart export with selective color coding to stay within API limits."""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.gc = None
        self.spreadsheet = None
        self._setup_google_sheets()
        
        # Color definitions - only essential colors
        self.colors = {
            'header_blue': {"red": 0.7, "green": 0.85, "blue": 1.0},    # Light blue for headers
            'stage_green': {"red": 0.85, "green": 1.0, "blue": 0.85},   # Light green for stages
            'ai_gray': {"red": 0.9, "green": 0.9, "blue": 0.9},         # Light gray for AI
            'red': {"red": 1.0, "green": 0.6, "blue": 0.6},             # Red for 0 scores
            'yellow': {"red": 1.0, "green": 1.0, "blue": 0.6},          # Yellow for 0.5 scores
            'green': {"red": 0.6, "green": 1.0, "blue": 0.6},           # Green for 1 scores
        }
        
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
                    'Выясняет сферу деятельности',
                    'Выяснил чем занимается компания, какая сфера деятельности',
                    'Какое количество сотрудников будет пользоваться услугами связи',
                    'Есть ли отдел продаж в компании',
                    'Кто отвечает за IT инфраструктуру в компании',
                    'Какие сервисы планируете подключать к интернету - почта, видеонаблюдение, телефония',
                    'Есть ли в компании дополнительные офисы в Москве или в других городах',
                    'Оборудование потребуется или нет',
                    'Требуется ли разводка для рабочих мест'
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
        """Export all manager data with smart color coding."""
        try:
            logger.info("Starting smart colored export of all manager data to Google Sheets")
            
            managers = self.db_service.get_all_managers()
            logger.info(f"Found {len(managers)} managers to export")
            
            for i, manager in enumerate(managers):
                logger.info(f"Processing manager {i+1}/{len(managers)}: {manager.name}")
                self._export_smart_colored_manager_sheet(manager)
                
                # Add delay between managers to avoid API limits
                if i < len(managers) - 1:
                    logger.info("Waiting 30 seconds to avoid API limits...")
                    time.sleep(30)
            
            # Create summary sheet
            self._create_smart_summary_sheet(managers)
            
            logger.info("Successfully exported all manager data with smart colors to Google Sheets")
            
        except Exception as e:
            logger.error(f"Error exporting manager data: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _export_smart_colored_manager_sheet(self, manager: Manager):
        """Export individual manager data with smart color coding."""
        try:
            sheet_name = f"Менеджер {manager.name}"
            logger.info(f"Exporting smart colored data for manager: {manager.name}")
            
            worksheet = self._get_or_create_worksheet(sheet_name)
            worksheet.clear()
            
            # Get manager's call records with analysis
            call_records = self._get_manager_call_records(manager.id)
            logger.info(f"Found {len(call_records)} call records for {manager.name}")
            
            # Prepare data in one batch
            all_data = self._prepare_smart_manager_data(manager, call_records)
            
            # Write all data in one batch operation
            if all_data:
                worksheet.update(all_data, value_input_option='USER_ENTERED')
                logger.info(f"Successfully wrote {len(all_data)} rows for {manager.name}")
                
                # Apply only essential formatting (limited colors)
                self._apply_smart_formatting(worksheet, manager, call_records)
            
            logger.info(f"Successfully exported smart colored data for {manager.name}")
                
        except Exception as e:
            logger.error(f"Error exporting manager {manager.name}: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _prepare_smart_manager_data(self, manager: Manager, call_records: List[tuple]) -> List[List[str]]:
        """Prepare all manager data as a single batch with score indicators."""
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
            call_data = self._format_smart_call_analysis(call_record, checklist_analysis, ai_analysis)
            data.extend(call_data)
            data.append([])  # Add spacing between calls
        
        return data
    
    def _format_smart_call_analysis(self, call_record: CallRecord, 
                                  checklist_analysis: Optional[ChecklistAnalysis],
                                  ai_analysis: Optional[AIAnalysis]) -> List[List[str]]:
        """Format call analysis with score indicators for smart coloring."""
        data = []
        
        # Call header
        data.append([f"ЗВОНОК: {call_record.file_name}"])
        data.append([
            f"Дата: {call_record.call_date.strftime('%Y-%m-%d %H:%M:%S') if call_record.call_date else 'Не указана'}",
            "",
            f"Тип: {call_record.call_type or 'Не указан'}"
        ])
        data.append([])
        
        # Detailed checklist analysis with visual indicators
        if checklist_analysis:
            data.extend(self._format_smart_checklist(checklist_analysis))
        
        # AI analysis with visual indicators
        if ai_analysis:
            data.extend(self._format_smart_ai_analysis(ai_analysis))
        
        return data
    
    def _format_smart_checklist(self, checklist: ChecklistAnalysis) -> List[List[str]]:
        """Format checklist with visual score indicators."""
        data = []
        
        # Checklist header
        data.append(["ЧЕК-ЛИСТ АНАЛИЗ"])
        data.append([])
        
        # Get individual scores for each criterion
        criterion_values = self._get_individual_criterion_scores(checklist)
        
        # Format each stage with detailed breakdown and indicators
        for stage_key, stage_info in self.checklist_criteria.items():
            # Stage header with totals
            stage_total = getattr(checklist, f"{stage_key}_total")
            max_score = len(stage_info['criteria'])
            percentage = (float(stage_total) / max_score) * 100 if max_score > 0 else 0
            
            # Add visual indicator for stage performance
            indicator = "🟢" if percentage >= 80 else "🟡" if percentage >= 60 else "🔴"
            
            data.append([
                f"{indicator} {stage_info['name']}",
                f"{float(stage_total):.1f}/{max_score}",
                f"{percentage:.1f}%"
            ])
            
            # Individual criteria with color indicators
            stage_values = criterion_values.get(stage_key, [])
            for i, criterion_name in enumerate(stage_info['criteria']):
                score = stage_values[i] if i < len(stage_values) else 0
                
                # Add emoji indicator based on score
                if float(score) >= 1.0:
                    score_indicator = "🟢"  # Green circle for 1.0
                elif float(score) >= 0.5:
                    score_indicator = "🟡"  # Yellow circle for 0.5
                else:
                    score_indicator = "🔴"  # Red circle for 0
                
                data.append([
                    "",
                    f"{score_indicator} {criterion_name}",
                    f"{float(score):.1f}"
                ])
            
            data.append([])  # Spacing between stages
        
        return data
    
    def _format_smart_ai_analysis(self, ai_analysis: AIAnalysis) -> List[List[str]]:
        """Format AI analysis with performance indicators."""
        data = []
        
        # AI Analysis header
        data.append(["AI АНАЛИЗ"])
        data.append([])
        
        # AI categories with scores and visual indicators
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
                # Add visual indicator for AI score
                score_val = float(score)
                indicator = "🟢" if score_val >= 80 else "🟡" if score_val >= 60 else "🔴"
                
                data.append([
                    f"{indicator} {category_name}",
                    f"{score_val:.1f}%",
                    explanation or ""
                ])
        
        # Additional AI data
        data.append([])
        if ai_analysis.summary:
            data.append(["📝 Краткое резюме:", ai_analysis.summary])
        
        if ai_analysis.client_name:
            data.append(["👤 Имя клиента:", ai_analysis.client_name])
        
        if ai_analysis.manager_responsible:
            data.append(["👨‍💼 Ответственный менеджер:", ai_analysis.manager_responsible])
        
        return data
    
    def _apply_smart_formatting(self, worksheet, manager: Manager, call_records: List[tuple]):
        """Apply minimal but effective formatting to key elements only."""
        try:
            logger.info("Applying smart formatting to key elements")
            
            # Only format headers and critical elements to stay within API limits
            format_requests = []
            
            # Format manager header
            format_requests.append({
                'range': 'A1:C1',
                'format': {
                    "backgroundColor": self.colors['header_blue'],
                    "textFormat": {"bold": True, "fontSize": 14}
                }
            })
            
            # Apply formatting in small batches with longer delays
            batch_size = 5
            for i in range(0, len(format_requests), batch_size):
                batch = format_requests[i:i + batch_size]
                
                for format_request in batch:
                    try:
                        worksheet.format(format_request['range'], format_request['format'])
                        time.sleep(2)  # Longer delay between format requests
                    except Exception as e:
                        logger.warning(f"Skipping format for {format_request['range']}: {e}")
            
            logger.info("Successfully applied smart formatting")
            
        except Exception as e:
            logger.warning(f"Could not apply all formatting: {e}")
    
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
                float(checklist.need_finds_business_area or 0),
                float(checklist.need_company_activity or 0),
                float(checklist.need_employee_count or 0),
                float(checklist.need_sales_department or 0),
                float(checklist.need_it_responsible or 0),
                float(checklist.need_services_to_connect or 0),
                float(checklist.need_additional_offices or 0),
                float(checklist.need_equipment_required or 0),
                float(checklist.need_workplace_wiring or 0)
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
    
    def _create_smart_summary_sheet(self, managers: List[Manager]):
        """Create summary sheet with emoji indicators."""
        try:
            sheet_name = "Общая сводка"
            logger.info("Creating smart colored summary sheet")
            
            worksheet = self._get_or_create_worksheet(sheet_name)
            worksheet.clear()
            
            # Prepare summary data with indicators
            summary_data = []
            
            # Header
            summary_data.append(["📊 ОБЩАЯ СВОДКА ПО МЕНЕДЖЕРАМ"])
            summary_data.append([f"📅 Дата создания: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"])
            summary_data.append([])
            
            # Column headers
            headers = ["Менеджер", "Email", "Отдел", "Статус", "Всего звонков", "Средний балл ЧЛ", "Средний балл AI"]
            summary_data.append(headers)
            
            # Manager data with performance indicators
            for manager in managers:
                stats = self.db_service.get_manager_statistics(manager.name, 365)
                
                checklist_score = stats.get('avg_checklist_score', 0)
                ai_score = stats.get('avg_ai_score', 0)
                
                # Add performance indicators
                checklist_percentage = (checklist_score / 33) * 100  # Max checklist score is 33
                checklist_indicator = "🟢" if checklist_percentage >= 80 else "🟡" if checklist_percentage >= 60 else "🔴"
                ai_indicator = "🟢" if ai_score >= 80 else "🟡" if ai_score >= 60 else "🔴"
                
                manager_data = [
                    f"{checklist_indicator if checklist_score > ai_score else ai_indicator} {manager.name}",
                    manager.email or "",
                    manager.department or "",
                    manager.status,
                    stats.get('total_calls', 0),
                    f"{checklist_indicator} {checklist_score:.1f}",
                    f"{ai_indicator} {ai_score:.1f}"
                ]
                summary_data.append(manager_data)
            
            # Write all data
            worksheet.update(summary_data, value_input_option='USER_ENTERED')
            
            # Apply minimal formatting for headers only
            try:
                worksheet.format('A1:G1', {
                    "backgroundColor": self.colors['header_blue'],
                    "textFormat": {"bold": True, "fontSize": 14}
                })
                time.sleep(2)
                worksheet.format('A4:G4', {
                    "backgroundColor": self.colors['stage_green'],
                    "textFormat": {"bold": True}
                })
            except Exception as e:
                logger.warning(f"Could not apply summary formatting: {e}")
            
            logger.info("Successfully created smart colored summary sheet")
                
        except Exception as e:
            logger.error(f"Error creating summary sheet: {e}")


def main():
    """Main function for smart colored export."""
    exporter = SmartColoredExporter()
    exporter.export_all_manager_data()


if __name__ == "__main__":
    main()