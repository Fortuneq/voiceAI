"""
Manager detection service based on regex patterns from n8n workflow.
"""

import re
from typing import Optional
from loguru import logger

from config import config
from models import ManagerDetectionResult


class ManagerDetectionService:
    """Service for detecting which manager is speaking in the dialogue."""
    
    def __init__(self):
        """Initialize manager detection service."""
        self.managers = config.managers
        
    def detect_manager(self, dialogue_text: str) -> ManagerDetectionResult:
        """
        Detect manager using exact regex patterns from n8n workflow.
        
        The n8n workflow uses regex operation to check for manager names:
        - "Владимир" -> outputKey: "Владимир"
        - "Надежда" -> outputKey: "Надежда" 
        - "Елизавета" -> outputKey: "Елизавета"
        """
        
        # Check for each manager name using case-sensitive regex
        # This replicates the exact logic from the n8n Switch node
        
        # Check for Владимир
        vladimir_pattern = r"Владимир"
        if re.search(vladimir_pattern, dialogue_text):
            logger.info("Detected manager: Владимир")
            return ManagerDetectionResult(
                detected_manager="Владимир",
                confidence=1.0
            )
        
        # Check for Надежда
        nadezhda_pattern = r"Надежда"
        if re.search(nadezhda_pattern, dialogue_text):
            logger.info("Detected manager: Надежда") 
            return ManagerDetectionResult(
                detected_manager="Надежда",
                confidence=1.0
            )
        
        # Check for Елизавета
        elizaveta_pattern = r"Елизавета"
        if re.search(elizaveta_pattern, dialogue_text):
            logger.info("Detected manager: Елизавета")
            return ManagerDetectionResult(
                detected_manager="Елизавета", 
                confidence=1.0
            )
        
        # If no manager detected, default to Елизавета (based on n8n flow structure)
        logger.warning("No manager name detected in dialogue, defaulting to Елизавета")
        return ManagerDetectionResult(
            detected_manager="Елизавета",
            confidence=0.5
        )
    
    def get_sheet_name_for_manager(self, manager_name: str) -> str:
        """Get the appropriate sheet name for a detected manager."""
        sheet_mapping = {
            "Владимир": config.vladimir_sheet_name,
            "Надежда": config.nadezhda_sheet_name,
            "Елизавета": config.elizaveta_sheet_name
        }
        
        return sheet_mapping.get(manager_name, config.elizaveta_sheet_name)
    
    def validate_manager_name(self, manager_name: str) -> bool:
        """Validate if the manager name is in the configured list."""
        return manager_name in self.managers
    
    def get_manager_stats(self, dialogue_text: str) -> dict:
        """Get statistics about manager name mentions in the dialogue."""
        stats = {}
        
        for manager in self.managers:
            pattern = re.compile(manager, re.IGNORECASE)
            matches = pattern.findall(dialogue_text)
            stats[manager] = {
                "count": len(matches),
                "found": len(matches) > 0
            }
        
        return stats