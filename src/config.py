"""
Configuration management for VoiceAI Call Analysis System.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config(BaseSettings):
    """Application configuration settings."""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    
    # Google APIs Configuration
    google_service_account_file: str = Field(..., env="GOOGLE_SERVICE_ACCOUNT_FILE")
    
    # Google Drive Configuration
    google_drive_folder_id: str = Field(
        default="1qb_o_yLNWVR8_LK98zKHstuEDNxNmGJW", 
        env="GOOGLE_DRIVE_FOLDER_ID"
    )
    
    # Google Sheets Configuration
    google_spreadsheet_id: str = Field(
        default="1V2ERVA_VOraJiRTxCrSW1AUQeBYUG3XkFldQQTqrU5w",
        env="GOOGLE_SPREADSHEET_ID"
    )
    
    # Sheet names for each manager
    elizaveta_sheet_name: str = Field(
        default="Входящие Елизавета",
        env="ELIZAVETA_SHEET_NAME"
    )
    vladimir_sheet_name: str = Field(
        default="Входящие Владимир", 
        env="VLADIMIR_SHEET_NAME"
    )
    nadezhda_sheet_name: str = Field(
        default="Входящие Надежда",
        env="NADEZHDA_SHEET_NAME"
    )
    analysis_sheet_name: str = Field(
        default="Анализ звонков",
        env="ANALYSIS_SHEET_NAME"
    )
    
    # Processing settings
    poll_interval_seconds: int = Field(default=60, env="POLL_INTERVAL_SECONDS")
    audio_temp_dir: str = Field(default="./temp_audio", env="AUDIO_TEMP_DIR")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Manager names for detection
    managers: list[str] = ["Елизавета", "Владимир", "Надежда"]
    company_name: str = "Весткол"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


# Global configuration instance
config = Config()

# Ensure temp directory exists
Path(config.audio_temp_dir).mkdir(exist_ok=True)