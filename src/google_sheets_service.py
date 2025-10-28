"""
Google Sheets service for saving call analysis results.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from loguru import logger

from .config import config
from .models import CallQualityScore, ProcessingResult, CallAnalysisResult


class GoogleSheetsService:
    """Service for interacting with Google Sheets API."""
    
    def __init__(self):
        """Initialize Google Sheets service."""
        self.credentials = self._get_credentials()
        self.client = gspread.authorize(self.credentials)
        self.spreadsheet_id = config.google_spreadsheet_id
        self.spreadsheet = None
        self._initialize_spreadsheet()
        
    def _get_credentials(self) -> Credentials:
        """Get Google API credentials from service account file."""
        try:
            credentials = Credentials.from_service_account_file(
                config.google_service_account_file,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            logger.info("Successfully loaded Google Sheets credentials")
            return credentials
        except Exception as e:
            logger.error(f"Failed to load Google Sheets credentials: {e}")
            raise
    
    def _initialize_spreadsheet(self):
        """Initialize connection to the spreadsheet."""
        try:
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            logger.info(f"Successfully connected to spreadsheet: {self.spreadsheet.title}")
        except Exception as e:
            logger.error(f"Failed to open spreadsheet: {e}")
            raise
    
    def append_call_analysis(self, result: ProcessingResult) -> bool:
        """
        Append call analysis results to the appropriate manager's sheet.
        
        This replicates the exact data mapping from the n8n workflow.
        """
        try:
            # Get the appropriate sheet name for the detected manager
            sheet_name = self._get_sheet_name_for_manager(result.detected_manager)
            worksheet = self.spreadsheet.worksheet(sheet_name)
            
            # Prepare row data exactly as mapped in n8n workflow
            row_data = self._prepare_call_quality_row(result)
            
            # Append the row
            worksheet.append_row(row_data, value_input_option='USER_ENTERED')
            
            logger.info(f"Successfully appended call analysis to {sheet_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to append call analysis: {e}")
            return False
    
    def append_detailed_analysis(self, result: ProcessingResult) -> bool:
        """
        Append detailed analysis results to the analysis sheet.
        
        This handles the second analysis workflow branch.
        """
        try:
            if not result.detailed_analysis:
                logger.warning("No detailed analysis to append")
                return False
                
            worksheet = self.spreadsheet.worksheet(config.analysis_sheet_name)
            
            # Prepare row data for detailed analysis
            row_data = self._prepare_detailed_analysis_row(result)
            
            # Append the row
            worksheet.append_row(row_data, value_input_option='USER_ENTERED')
            
            logger.info(f"Successfully appended detailed analysis to {config.analysis_sheet_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to append detailed analysis: {e}")
            return False
    
    def _get_sheet_name_for_manager(self, manager_name: str) -> str:
        """Get the appropriate sheet name for a manager."""
        sheet_mapping = {
            "Владимир": config.vladimir_sheet_name,
            "Надежда": config.nadezhda_sheet_name,
            "Елизавета": config.elizaveta_sheet_name
        }
        
        return sheet_mapping.get(manager_name, config.elizaveta_sheet_name)
    
    def _prepare_call_quality_row(self, result: ProcessingResult) -> List[Any]:
        """
        Prepare row data for call quality analysis.
        
        This replicates the exact column mapping from the n8n workflow's Google Sheets nodes.
        """
        quality_scores = result.quality_scores
        detailed_scores = quality_scores.detailed_scores
        
        # Extract detailed scores by category - exactly as mapped in n8n workflow
        greeting_scores = detailed_scores.get("Этап ПРИВЕТСТВИЕ", {})
        contact_scores = detailed_scores.get("Этап УСТАНОВЛЕНИЕ КОНТАКТА", {})
        programming_scores = detailed_scores.get("Этап ПРОГРАММИРОВАНИЯ", {})
        needs_scores = detailed_scores.get("Этап СОЗДАНИЯ ПОТРЕБНОСТИ", {})
        presentation_scores = detailed_scores.get("Этап ПРЕЗЕНТАЦИЯ", {})
        objections_scores = detailed_scores.get("Этап РАБОТА С СОМНЕНИЯМИ", {})
        closing_scores = detailed_scores.get("ЭТАП ЗАВЕРШЕНИЯ", {})
        
        # Row data following the exact order from n8n column mapping
        row_data = [
            # Greeting stage
            greeting_scores.get("Время до соединения с менеджером", ""),
            greeting_scores.get("Корпоративное приветсвие", ""),
            greeting_scores.get("Тон добродушный, приветливый, есть улыбка в голосе", ""),
            greeting_scores.get("Не тараторит, не съедает слова", ""),
            greeting_scores.get("Озвучивает цель звонка инфоповод", ""),
            greeting_scores.get("Не использует фразу 'вам удобно разговаривать'", ""),
            greeting_scores.get("Не использует фразу 'как к вам можно обращаться'", ""),
            
            # Transcription
            result.tagged_dialogue.content,
            
            # Contact establishment stage
            contact_scores.get("Обращается по имени, минимум 2 раза", ""),
            contact_scores.get("Не перебивает, дослушивает до конца", ""),
            contact_scores.get("Говорит на простом понятном языке", ""),
            contact_scores.get("Отсутствует сухой формальный тон", ""),
            contact_scores.get("Общается на 'равных'", ""),
            contact_scores.get("Использует приемы Small talk", ""),
            contact_scores.get("Говорит комплимент, похвалу", ""),
            contact_scores.get("Использует юмор", ""),
            
            # Needs creation stage  
            needs_scores.get("Задал обязательные вопросы", ""),
            needs_scores.get("Делает презентацию компании", ""),
            
            # Closing stage
            closing_scores.get("Резюмировал разговор", ""),
            
            # Total score
            quality_scores.total_score,
            
            # More closing fields
            closing_scores.get("Уточняет куда отправить КП", ""),
            closing_scores.get("Спросить к какой дате нужна услуга", ""),
            closing_scores.get("Озвучивает следующие шаги", ""),
            closing_scores.get("Оставил контакты и поблагодарил", ""),
            closing_scores.get("Уточняет остались ли вопросы", ""),
            
            # Objections handling
            objections_scores.get("Не спорит с клиентом", ""),
            objections_scores.get("Предлагает отправить КП после отработки", ""),
            objections_scores.get("Аргументы соответствуют возражению", ""),
            objections_scores.get("Присоединяется при отработке возражений", ""),
            objections_scores.get("Отрабатывает все возражения", ""),
            
            # Presentation stage
            presentation_scores.get("Менеджер знает продукт", ""),
            presentation_scores.get("Предлагает отправить КП или тестовый период", ""),
            presentation_scores.get("Рассказывает о кейсах или отзывах", ""),
            presentation_scores.get("Делает презентацию 2-3 услуг", ""),
            
            # Programming stage
            programming_scores.get("Использует программирование в начале разговора", ""),
            programming_scores.get("На протяжении всего диалога менеджер 'ведет'", ""),
            
            # More needs creation fields
            needs_scores.get("Не говорит 'Мы оператор/провайдер интернет услуг'", ""),
            needs_scores.get("Выясняет чем занимается компания", ""),
            needs_scores.get("Выясняет подключена ли услуга интернет", ""),
            needs_scores.get("Если все устраивает, узнает про резервный канал", ""),
            needs_scores.get("Узнает о случаях атак", ""),
            needs_scores.get("Задает вопросы про доп. услуги", ""),
            
            # Stage totals
            greeting_scores.get("Итого", ""),
            contact_scores.get("Итого", ""),
            programming_scores.get("Итого", ""),
            needs_scores.get("Итого", ""),
            presentation_scores.get("Итого", ""),
            objections_scores.get("Итого", ""),
            closing_scores.get("Итого", ""),
        ]
        
        return row_data
    
    def _prepare_detailed_analysis_row(self, result: ProcessingResult) -> List[Any]:
        """
        Prepare row data for detailed analysis.
        
        This would map the detailed analysis fields to sheet columns.
        """
        analysis = result.detailed_analysis
        if not analysis:
            return []
        
        # This would need to be implemented based on the specific sheet structure
        # for detailed analysis results
        row_data = [
            result.audio_file.name,
            result.processing_timestamp.isoformat(),
            analysis.summary if analysis else "",
            # Add other fields as needed
        ]
        
        return row_data
    
    def get_worksheet_headers(self, sheet_name: str) -> Optional[List[str]]:
        """Get the headers from a specific worksheet."""
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            headers = worksheet.row_values(1)
            return headers
        except Exception as e:
            logger.error(f"Failed to get headers from {sheet_name}: {e}")
            return None
    
    def clear_worksheet(self, sheet_name: str) -> bool:
        """Clear all data from a worksheet (keeping headers)."""
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            worksheet.clear()
            logger.info(f"Cleared worksheet: {sheet_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear worksheet {sheet_name}: {e}")
            return False
    
    def get_last_row_number(self, sheet_name: str) -> int:
        """Get the number of the last row with data in a worksheet."""
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            return len(worksheet.get_all_values())
        except Exception as e:
            logger.error(f"Failed to get last row for {sheet_name}: {e}")
            return 0