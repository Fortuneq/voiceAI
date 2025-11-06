#!/usr/bin/env python3
"""
Google Sheets Exporter with optimized color coding.
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


class ColoredSheetsExporter:
    """Export with optimized color coding using batch formatting."""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.gc = None
        self.spreadsheet = None
        self._setup_google_sheets()
        
        # Color definitions
        self.colors = {
            'red': {"red": 1.0, "green": 0.4, "blue": 0.4},      # 0 score
            'yellow': {"red": 1.0, "green": 1.0, "blue": 0.4},   # 0.5 score
            'green': {"red": 0.4, "green": 0.8, "blue": 0.4},    # 1 score
            'light_blue': {"red": 0.9, "green": 0.95, "blue": 1.0},  # Headers
            'light_green': {"red": 0.9, "green": 1.0, "blue": 0.9},  # Stage headers
            'light_gray': {"red": 0.95, "green": 0.95, "blue": 0.95}  # AI headers
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
        """Export all manager data with color coding."""
        try:
            logger.info("Starting colored export of all manager data to Google Sheets")
            
            managers = self.db_service.get_all_managers()
            logger.info(f"Found {len(managers)} managers to export")
            
            for i, manager in enumerate(managers):
                logger.info(f"Processing manager {i+1}/{len(managers)}: {manager.name}")
                self._export_colored_manager_sheet(manager)
                
                # Add delay between managers to avoid API limits
                if i < len(managers) - 1:
                    logger.info("Waiting 20 seconds to avoid API limits...")
                    time.sleep(20)
            
            # Create summary sheet
            self._create_summary_sheet(managers)
            
            logger.info("Successfully exported all manager data with colors to Google Sheets")
            
        except Exception as e:
            logger.error(f"Error exporting manager data: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _export_colored_manager_sheet(self, manager: Manager):
        """Export individual manager data with color coding."""
        try:
            sheet_name = f"Менеджер {manager.name}"
            logger.info(f"Exporting colored data for manager: {manager.name}")
            
            worksheet = self._get_or_create_worksheet(sheet_name)
            worksheet.clear()
            
            # Get manager's call records with analysis
            call_records = self._get_manager_call_records(manager.id)
            logger.info(f"Found {len(call_records)} call records for {manager.name}")
            
            # Prepare data and formatting information
            data, format_requests = self._prepare_colored_manager_data(manager, call_records)
            
            # Write all data in one batch
            if data:
                worksheet.update(data, value_input_option='USER_ENTERED')
                logger.info(f"Successfully wrote {len(data)} rows for {manager.name}")
                
                # Apply colors in batches
                self._apply_batch_formatting(worksheet, format_requests)
            
            logger.info(f"Successfully exported colored data for {manager.name}")
                
        except Exception as e:
            logger.error(f"Error exporting manager {manager.name}: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _prepare_colored_manager_data(self, manager: Manager, call_records: List[tuple]) -> Tuple[List[List[str]], List[Dict]]:
        """Prepare data and collect formatting information."""
        data = []
        format_requests = []
        row = 1
        
        # Manager info header
        data.append([f"МЕНЕДЖЕР: {manager.name}"])
        format_requests.append({
            'range': f'A{row}:C{row}',
            'format': {
                "backgroundColor": self.colors['light_blue'],
                "textFormat": {"bold": True, "fontSize": 14}
            }
        })
        row += 1
        
        data.append([f"Email: {manager.email or 'Не указан'}"])
        row += 1
        data.append([f"Отдел: {manager.department or 'Не указан'}"])
        row += 1
        data.append([f"Статус: {manager.status}"])
        row += 1
        data.append([f"Дата создания отчета: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"])
        row += 1
        data.append([])  # Empty row
        row += 1
        
        # Process each call record
        for call_record, checklist_analysis, ai_analysis in call_records:
            call_data, call_formats, new_row = self._format_call_with_colors(
                call_record, checklist_analysis, ai_analysis, row
            )
            data.extend(call_data)
            format_requests.extend(call_formats)
            row = new_row
            
            data.append([])  # Add spacing between calls
            row += 1
        
        return data, format_requests
    
    def _format_call_with_colors(self, call_record: CallRecord, 
                               checklist_analysis: Optional[ChecklistAnalysis],
                               ai_analysis: Optional[AIAnalysis],
                               start_row: int) -> Tuple[List[List[str]], List[Dict], int]:
        """Format call data with color information."""
        data = []
        format_requests = []
        row = start_row
        
        # Call header
        data.append([f"ЗВОНОК: {call_record.file_name}"])
        format_requests.append({
            'range': f'A{row}:D{row}',
            'format': {
                "backgroundColor": self.colors['light_blue'],
                "textFormat": {"bold": True, "fontSize": 12}
            }
        })
        row += 1
        
        data.append([
            f"Дата: {call_record.call_date.strftime('%Y-%m-%d %H:%M:%S') if call_record.call_date else 'Не указана'}",
            "",
            f"Тип: {call_record.call_type or 'Не указан'}"
        ])
        row += 1
        data.append([])
        row += 1
        
        # Detailed checklist analysis with colors
        if checklist_analysis:
            checklist_data, checklist_formats, row = self._format_checklist_with_colors(
                checklist_analysis, row
            )
            data.extend(checklist_data)
            format_requests.extend(checklist_formats)
        
        # AI analysis with colors
        if ai_analysis:
            ai_data, ai_formats, row = self._format_ai_analysis_with_colors(ai_analysis, row)
            data.extend(ai_data)
            format_requests.extend(ai_formats)
        
        return data, format_requests, row
    
    def _format_checklist_with_colors(self, checklist: ChecklistAnalysis, start_row: int) -> Tuple[List[List[str]], List[Dict], int]:
        """Format checklist with color coding."""
        data = []
        format_requests = []
        row = start_row
        
        # Checklist header
        data.append(["ЧЕК-ЛИСТ АНАЛИЗ"])
        format_requests.append({
            'range': f'A{row}:C{row}',
            'format': {
                "backgroundColor": self.colors['light_green'],
                "textFormat": {"bold": True, "fontSize": 12}
            }
        })
        row += 1
        data.append([])
        row += 1
        
        # Get individual scores for each criterion
        criterion_values = self._get_individual_criterion_scores(checklist)
        
        # Format each stage with colored breakdown
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
            
            # Color code the stage total based on percentage
            stage_color = self._get_color_for_percentage(percentage)
            format_requests.append({
                'range': f'B{row}:C{row}',
                'format': {"backgroundColor": stage_color}
            })
            row += 1
            
            # Individual criteria with color coding
            stage_values = criterion_values.get(stage_key, [])
            for i, criterion_name in enumerate(stage_info['criteria']):
                score = stage_values[i] if i < len(stage_values) else 0
                
                data.append([
                    "",
                    criterion_name,
                    f"{float(score):.1f}"
                ])
                
                # Color code individual criterion
                criterion_color = self._get_color_for_score(float(score))
                format_requests.append({
                    'range': f'C{row}',
                    'format': {"backgroundColor": criterion_color}
                })
                row += 1
            
            data.append([])  # Spacing between stages
            row += 1
        
        return data, format_requests, row
    
    def _format_ai_analysis_with_colors(self, ai_analysis: AIAnalysis, start_row: int) -> Tuple[List[List[str]], List[Dict], int]:
        """Format AI analysis with color coding."""
        data = []
        format_requests = []
        row = start_row
        
        # AI Analysis header
        data.append(["AI АНАЛИЗ"])
        format_requests.append({
            'range': f'A{row}:C{row}',
            'format': {
                "backgroundColor": self.colors['light_gray'],
                "textFormat": {"bold": True, "fontSize": 12}
            }
        })
        row += 1
        data.append([])
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
                data.append([
                    category_name,
                    f"{float(score):.1f}%",
                    explanation or ""
                ])
                
                # Color code AI score based on percentage
                ai_color = self._get_color_for_percentage(float(score))
                format_requests.append({
                    'range': f'B{row}',
                    'format': {"backgroundColor": ai_color}
                })
                row += 1
        
        # Additional AI data
        data.append([])
        row += 1
        
        if ai_analysis.summary:
            data.append(["Краткое резюме:", ai_analysis.summary])
            row += 1
        
        if ai_analysis.client_name:
            data.append(["Имя клиента:", ai_analysis.client_name])
            row += 1
        
        if ai_analysis.manager_responsible:
            data.append(["Ответственный менеджер:", ai_analysis.manager_responsible])
            row += 1
        
        return data, format_requests, row
    
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
    
    def _get_color_for_score(self, score: float) -> Dict[str, float]:
        """Get color based on score (0, 0.5, 1)."""
        if score >= 1.0:
            return self.colors['green']   # Green for score 1
        elif score >= 0.5:
            return self.colors['yellow']  # Yellow for score 0.5
        else:
            return self.colors['red']     # Red for score 0
    
    def _get_color_for_percentage(self, percentage: float) -> Dict[str, float]:
        """Get color based on percentage."""
        if percentage >= 80:
            return self.colors['green']   # Green for good performance
        elif percentage >= 60:
            return self.colors['yellow']  # Yellow for average performance
        else:
            return self.colors['red']     # Red for poor performance
    
    def _apply_batch_formatting(self, worksheet, format_requests: List[Dict]):
        """Apply formatting in optimized batches."""
        try:
            logger.info(f"Applying {len(format_requests)} color formats in batches")
            
            # Group format requests into batches of 20 to avoid API limits
            batch_size = 20
            for i in range(0, len(format_requests), batch_size):
                batch = format_requests[i:i + batch_size]
                
                # Apply each format in the batch
                for format_request in batch:
                    try:
                        worksheet.format(format_request['range'], format_request['format'])
                    except Exception as e:
                        logger.warning(f"Failed to apply format to {format_request['range']}: {e}")
                
                # Small delay between batches
                if i + batch_size < len(format_requests):
                    time.sleep(1)
            
            logger.info("Successfully applied color formatting")
            
        except Exception as e:
            logger.warning(f"Could not apply all formatting: {e}")
    
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
        """Create summary sheet with color coding."""
        try:
            sheet_name = "Общая сводка"
            logger.info("Creating colored summary sheet")
            
            worksheet = self._get_or_create_worksheet(sheet_name)
            worksheet.clear()
            
            # Prepare summary data
            summary_data = []
            format_requests = []
            
            # Header
            summary_data.append(["Общая сводка по менеджерам"])
            format_requests.append({
                'range': 'A1:G1',
                'format': {
                    "backgroundColor": self.colors['light_blue'],
                    "textFormat": {"bold": True, "fontSize": 14}
                }
            })
            
            summary_data.append([f"Дата создания: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"])
            summary_data.append([])
            
            # Column headers
            headers = ["Менеджер", "Email", "Отдел", "Статус", "Всего звонков", "Средний балл ЧЛ", "Средний балл AI"]
            summary_data.append(headers)
            format_requests.append({
                'range': 'A4:G4',
                'format': {
                    "backgroundColor": self.colors['light_gray'],
                    "textFormat": {"bold": True}
                }
            })
            
            # Manager data with color coding
            row = 5
            for manager in managers:
                stats = self.db_service.get_manager_statistics(manager.name, 365)
                
                checklist_score = stats.get('avg_checklist_score', 0)
                ai_score = stats.get('avg_ai_score', 0)
                
                manager_data = [
                    manager.name,
                    manager.email or "",
                    manager.department or "",
                    manager.status,
                    stats.get('total_calls', 0),
                    f"{checklist_score:.1f}",
                    f"{ai_score:.1f}"
                ]
                summary_data.append(manager_data)
                
                # Color code the scores
                checklist_percentage = (checklist_score / 33) * 100  # Max checklist score is 33
                ai_percentage = ai_score
                
                format_requests.append({
                    'range': f'F{row}',
                    'format': {"backgroundColor": self._get_color_for_percentage(checklist_percentage)}
                })
                format_requests.append({
                    'range': f'G{row}',
                    'format': {"backgroundColor": self._get_color_for_percentage(ai_percentage)}
                })
                
                row += 1
            
            # Write all data and apply formatting
            worksheet.update(summary_data, value_input_option='USER_ENTERED')
            self._apply_batch_formatting(worksheet, format_requests)
            
            logger.info("Successfully created colored summary sheet")
                
        except Exception as e:
            logger.error(f"Error creating summary sheet: {e}")


def main():
    """Main function for colored export."""
    exporter = ColoredSheetsExporter()
    exporter.export_all_manager_data()


if __name__ == "__main__":
    main()