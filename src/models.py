"""
Data models for VoiceAI Call Analysis System.
"""

from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


class AudioFile(BaseModel):
    """Model for audio file information."""
    id: str
    name: str
    modified_time: datetime
    size: int
    mime_type: str


class TranscriptionResult(BaseModel):
    """Model for transcription result."""
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None


class RoleTaggedDialogue(BaseModel):
    """Model for dialogue with role tags."""
    content: str
    original_text: str
    timestamp: datetime = Field(default_factory=datetime.now)


class CallQualityScore(BaseModel):
    """Model for call quality analysis scores."""
    # Overall total
    total_score: float = Field(alias="ВСЕГО")
    
    # Call type
    call_type: str = Field(alias="Тип звонка")
    
    # Individual scores
    greeting_score: float = Field(default=0.0, alias="ПРИВЕТСТВИЕ")
    contact_score: float = Field(default=0.0, alias="УСТАНОВЛЕНИЕ КОНТАКТА") 
    presentation_score: float = Field(default=0.0, alias="ПРЕЗЕНТАЦИЯ")
    objection_handling_score: float = Field(default=0.0, alias="РАБОТА С СОМНЕНИЯМИ")
    closing_score: float = Field(default=0.0, alias="ЗАВЕРШЕНИЕ")
    
    # Stage totals
    greeting_stage_total: float = Field(default=0.0, alias="ПРИВЕТСТВИЕ Всего")
    contact_stage_total: float = Field(default=0.0, alias="УСТАНОВЛЕНИЕ КОНТАКТА Всего")
    presentation_stage_total: float = Field(default=0.0, alias="ПРЕЗЕНТАЦИЯ Всего") 
    objection_stage_total: float = Field(default=0.0, alias="РАБОТА С СОМНЕНИЯМИ Всего")
    closing_stage_total: float = Field(default=0.0, alias="ЗАВЕРШЕНИЕ Всего")
    
    # Detailed scores by category
    detailed_scores: Dict[str, Any] = {}
    
    model_config = {
        "populate_by_name": True
    }


class EvaluationScore(BaseModel):
    """Model for evaluation scores with value and explanation."""
    value: float = Field(ge=0, le=100, description="Score from 0 to 100")
    explanation: str = Field(description="Detailed explanation of the score")


class CallAnalysisResult(BaseModel):
    """Model for detailed call analysis result using the structured format."""
    summary: str = Field(description="Краткое резюме разговора (5–15 предложений)")
    client_talks_most: str = Field(description="Кто говорил больше (да/нет + краткое пояснение)")
    client_name: str = Field(description="Имя клиента (по возможности ФИО)")
    style_adaptation: str = Field(description="Адаптация стиля менеджера под клиента (да/нет + пояснение)")
    target_client: str = Field(description="Целевой ли клиент для клуба (да/нет + пояснение)")
    client_needs: str = Field(description="Основные потребности и мотивация клиента")
    manager_responsible: str = Field(description="ФИО менеджера, который проводил встречу")
    
    # Evaluation scores with explanations
    contact_establishment: EvaluationScore = Field(description="Оценка установления контакта")
    qualification: EvaluationScore = Field(description="Оценка квалификации клиента")
    needs_identification: EvaluationScore = Field(description="Оценка выявления потребностей")
    product_presentation: EvaluationScore = Field(description="Оценка презентации продукта")
    objection_handling: EvaluationScore = Field(description="Оценка работы с возражениями")
    closing: EvaluationScore = Field(description="Оценка закрытия сделки")
    sale_probability: EvaluationScore = Field(description="Вероятность продажи")
    
    # Additional fields
    hidden_objections: str = Field(description="Скрытые возражения, которые не были отработаны")
    next_step: str = Field(description="Следующий шаг после встречи")


class StageScore(BaseModel):
    """Model for stage evaluation with individual criteria and total."""
    Total: float = Field(default=0.0)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-calculate total from all numeric fields except 'Total'
        total = 0
        for key, value in data.items():
            if key != "Total" and isinstance(value, (int, float)):
                total += value
        self.Total = total


class ChecklistAnalysisResult(BaseModel):
    """Model for checklist-based call analysis following the Excel structure."""
    call_type: str = Field(alias="Call Type")
    stage_greeting: Dict[str, Union[float, int]] = Field(alias="Stage GREETING") 
    stage_contact_establishment: Dict[str, Union[float, int]] = Field(alias="Stage CONTACT ESTABLISHMENT")
    stage_programming: Dict[str, Union[float, int]] = Field(alias="Stage PROGRAMMING")
    stage_need_identification: Dict[str, Union[float, int]] = Field(alias="Stage NEED IDENTIFICATION")
    stage_presentation: Dict[str, Union[float, int]] = Field(alias="Stage PRESENTATION")
    stage_handling_objections: Dict[str, Union[float, int]] = Field(alias="Stage HANDLING OBJECTIONS")
    stage_closing: Dict[str, Union[float, int]] = Field(alias="Stage CLOSING")
    overall_total: float = Field(alias="OVERALL TOTAL")
    
    model_config = {
        "populate_by_name": True
    }


class ProcessingResult(BaseModel):
    """Model for complete processing result."""
    audio_file: AudioFile
    transcription: TranscriptionResult
    tagged_dialogue: RoleTaggedDialogue
    quality_scores: CallQualityScore
    detailed_analysis: Optional[CallAnalysisResult] = None
    checklist_analysis: Optional[ChecklistAnalysisResult] = None
    detected_manager: str
    processing_timestamp: datetime = Field(default_factory=datetime.now)
    
    
class ManagerDetectionResult(BaseModel):
    """Model for manager detection result."""
    detected_manager: str
    confidence: float = 1.0