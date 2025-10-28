"""
SQLAlchemy database models for VoiceAI Call Analysis System.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DECIMAL, TIMESTAMP, ForeignKey, CheckConstraint, Index, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

Base = declarative_base()


class Manager(Base):
    """Manager model for storing manager information."""
    __tablename__ = 'managers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    email = Column(String(255))
    department = Column(String(100))
    hire_date = Column(TIMESTAMP)
    status = Column(String(20), default='active')
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    call_records = relationship("CallRecord", back_populates="manager", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive')", name='check_manager_status'),
        Index('idx_managers_name', 'name'),
        Index('idx_managers_status', 'status'),
    )


class CallRecord(Base):
    """Call record model for storing basic call information."""
    __tablename__ = 'call_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String(255), nullable=False, unique=True)  # Google Drive file ID
    file_name = Column(String(500), nullable=False)
    manager_id = Column(Integer, ForeignKey('managers.id'), nullable=False)
    call_type = Column(String(20), nullable=False)
    call_date = Column(TIMESTAMP)
    file_size = Column(BigInteger)
    mime_type = Column(String(100))
    transcription_text = Column(Text)
    tagged_dialogue = Column(Text)
    processing_status = Column(String(20), default='pending')
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    manager = relationship("Manager", back_populates="call_records")
    checklist_analysis = relationship("ChecklistAnalysis", back_populates="call_record", cascade="all, delete-orphan")
    ai_analysis = relationship("AIAnalysis", back_populates="call_record", cascade="all, delete-orphan")
    legacy_quality_scores = relationship("LegacyQualityScore", back_populates="call_record", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("call_type IN ('Входящий', 'Исходящий')", name='check_call_type'),
        CheckConstraint("processing_status IN ('pending', 'processing', 'completed', 'failed')", name='check_processing_status'),
        Index('idx_call_records_manager_id', 'manager_id'),
        Index('idx_call_records_call_type', 'call_type'),
        Index('idx_call_records_call_date', 'call_date'),
        Index('idx_call_records_file_id', 'file_id'),
    )


class ChecklistAnalysis(Base):
    """Checklist analysis model for storing detailed stage-by-stage scoring."""
    __tablename__ = 'checklist_analysis'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    call_record_id = Column(Integer, ForeignKey('call_records.id', ondelete='CASCADE'), nullable=False)
    
    # Stage GREETING scores
    greeting_time_before_manager = Column(DECIMAL(3,1), default=0)
    greeting_corporate_greeting = Column(DECIMAL(3,1), default=0)
    greeting_tone_friendly = Column(DECIMAL(3,1), default=0)
    greeting_no_rush_words = Column(DECIMAL(3,1), default=0)
    greeting_states_purpose = Column(DECIMAL(3,1), default=0)
    greeting_no_convenient_phrase = Column(DECIMAL(3,1), default=0)
    greeting_no_address_phrase = Column(DECIMAL(3,1), default=0)
    
    # Stage CONTACT ESTABLISHMENT scores
    contact_addresses_by_name = Column(DECIMAL(3,1), default=0)
    contact_no_interrupt = Column(DECIMAL(3,1), default=0)
    contact_simple_language = Column(DECIMAL(3,1), default=0)
    contact_avoids_formal_tone = Column(DECIMAL(3,1), default=0)
    contact_communicates_equal = Column(DECIMAL(3,1), default=0)
    contact_uses_small_talk = Column(DECIMAL(3,1), default=0)
    contact_gives_compliment = Column(DECIMAL(3,1), default=0)
    contact_uses_humor = Column(DECIMAL(3,1), default=0)
    
    # Stage PROGRAMMING scores
    programming_uses_at_start = Column(DECIMAL(3,1), default=0)
    programming_leads_conversation = Column(DECIMAL(3,1), default=0)
    
    # Stage NEED IDENTIFICATION scores
    need_asks_required_questions = Column(DECIMAL(3,1), default=0)
    need_finds_business_area = Column(DECIMAL(3,1), default=0)
    
    # Stage PRESENTATION scores
    presentation_presents_company = Column(DECIMAL(3,1), default=0)
    presentation_services_with_benefits = Column(DECIMAL(3,1), default=0)
    presentation_mentions_cases = Column(DECIMAL(3,1), default=0)
    presentation_offers_proposal = Column(DECIMAL(3,1), default=0)
    presentation_knows_product = Column(DECIMAL(3,1), default=0)
    
    # Stage HANDLING OBJECTIONS scores
    objections_handles_fully = Column(DECIMAL(3,1), default=0)
    objections_agrees_empathizes = Column(DECIMAL(3,1), default=0)
    objections_arguments_match = Column(DECIMAL(3,1), default=0)
    objections_no_argue = Column(DECIMAL(3,1), default=0)
    objections_offers_proposal = Column(DECIMAL(3,1), default=0)
    
    # Stage CLOSING scores
    closing_asks_questions_remain = Column(DECIMAL(3,1), default=0)
    closing_clarifies_proposal_send = Column(DECIMAL(3,1), default=0)
    closing_asks_service_date = Column(DECIMAL(3,1), default=0)
    closing_summarizes_conversation = Column(DECIMAL(3,1), default=0)
    closing_states_next_steps = Column(DECIMAL(3,1), default=0)
    closing_leaves_contacts = Column(DECIMAL(3,1), default=0)
    
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    call_record = relationship("CallRecord", back_populates="checklist_analysis")
    
    # Computed properties for totals
    @property
    def greeting_total(self) -> float:
        return (self.greeting_time_before_manager or 0) + (self.greeting_corporate_greeting or 0) + \
               (self.greeting_tone_friendly or 0) + (self.greeting_no_rush_words or 0) + \
               (self.greeting_states_purpose or 0) + (self.greeting_no_convenient_phrase or 0) + \
               (self.greeting_no_address_phrase or 0)
    
    @property
    def contact_total(self) -> float:
        return (self.contact_addresses_by_name or 0) + (self.contact_no_interrupt or 0) + \
               (self.contact_simple_language or 0) + (self.contact_avoids_formal_tone or 0) + \
               (self.contact_communicates_equal or 0) + (self.contact_uses_small_talk or 0) + \
               (self.contact_gives_compliment or 0) + (self.contact_uses_humor or 0)
    
    @property
    def programming_total(self) -> float:
        return (self.programming_uses_at_start or 0) + (self.programming_leads_conversation or 0)
    
    @property
    def need_total(self) -> float:
        return (self.need_asks_required_questions or 0) + (self.need_finds_business_area or 0)
    
    @property
    def presentation_total(self) -> float:
        return (self.presentation_presents_company or 0) + (self.presentation_services_with_benefits or 0) + \
               (self.presentation_mentions_cases or 0) + (self.presentation_offers_proposal or 0) + \
               (self.presentation_knows_product or 0)
    
    @property
    def objections_total(self) -> float:
        return (self.objections_handles_fully or 0) + (self.objections_agrees_empathizes or 0) + \
               (self.objections_arguments_match or 0) + (self.objections_no_argue or 0) + \
               (self.objections_offers_proposal or 0)
    
    @property
    def closing_total(self) -> float:
        return (self.closing_asks_questions_remain or 0) + (self.closing_clarifies_proposal_send or 0) + \
               (self.closing_asks_service_date or 0) + (self.closing_summarizes_conversation or 0) + \
               (self.closing_states_next_steps or 0) + (self.closing_leaves_contacts or 0)
    
    @property
    def overall_total(self) -> float:
        return self.greeting_total + self.contact_total + self.programming_total + \
               self.need_total + self.presentation_total + self.objections_total + self.closing_total
    
    __table_args__ = (
        Index('idx_checklist_analysis_call_record_id', 'call_record_id'),
    )


class AIAnalysis(Base):
    """AI analysis model for storing structured AI-based call analysis."""
    __tablename__ = 'ai_analysis'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    call_record_id = Column(Integer, ForeignKey('call_records.id', ondelete='CASCADE'), nullable=False)
    
    # Basic information
    summary = Column(Text)
    client_talks_most = Column(Text)
    client_name = Column(String(255))
    style_adaptation = Column(Text)
    target_client = Column(Text)
    client_needs = Column(Text)
    manager_responsible = Column(String(255))
    
    # Evaluation scores (0-100)
    contact_establishment_value = Column(DECIMAL(5,2))
    contact_establishment_explanation = Column(Text)
    
    qualification_value = Column(DECIMAL(5,2))
    qualification_explanation = Column(Text)
    
    needs_identification_value = Column(DECIMAL(5,2))
    needs_identification_explanation = Column(Text)
    
    product_presentation_value = Column(DECIMAL(5,2))
    product_presentation_explanation = Column(Text)
    
    objection_handling_value = Column(DECIMAL(5,2))
    objection_handling_explanation = Column(Text)
    
    closing_value = Column(DECIMAL(5,2))
    closing_explanation = Column(Text)
    
    sale_probability_value = Column(DECIMAL(5,2))
    sale_probability_explanation = Column(Text)
    
    # Additional fields
    hidden_objections = Column(Text)
    next_step = Column(Text)
    
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    call_record = relationship("CallRecord", back_populates="ai_analysis")
    
    # Computed property for average score
    @property
    def average_score(self) -> Optional[float]:
        scores = [
            self.contact_establishment_value,
            self.qualification_value,
            self.needs_identification_value,
            self.product_presentation_value,
            self.objection_handling_value,
            self.closing_value
        ]
        valid_scores = [score for score in scores if score is not None]
        return sum(valid_scores) / len(valid_scores) if valid_scores else None
    
    __table_args__ = (
        CheckConstraint("contact_establishment_value >= 0 AND contact_establishment_value <= 100", name='check_contact_establishment_value'),
        CheckConstraint("qualification_value >= 0 AND qualification_value <= 100", name='check_qualification_value'),
        CheckConstraint("needs_identification_value >= 0 AND needs_identification_value <= 100", name='check_needs_identification_value'),
        CheckConstraint("product_presentation_value >= 0 AND product_presentation_value <= 100", name='check_product_presentation_value'),
        CheckConstraint("objection_handling_value >= 0 AND objection_handling_value <= 100", name='check_objection_handling_value'),
        CheckConstraint("closing_value >= 0 AND closing_value <= 100", name='check_closing_value'),
        CheckConstraint("sale_probability_value >= 0 AND sale_probability_value <= 100", name='check_sale_probability_value'),
        Index('idx_ai_analysis_call_record_id', 'call_record_id'),
    )


class LegacyQualityScore(Base):
    """Legacy quality score model for backward compatibility."""
    __tablename__ = 'legacy_quality_scores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    call_record_id = Column(Integer, ForeignKey('call_records.id', ondelete='CASCADE'), nullable=False)
    call_type = Column(String(20))
    greeting_score = Column(DECIMAL(3,1), default=0)
    contact_score = Column(DECIMAL(3,1), default=0)
    presentation_score = Column(DECIMAL(3,1), default=0)
    objection_handling_score = Column(DECIMAL(3,1), default=0)
    closing_score = Column(DECIMAL(3,1), default=0)
    greeting_stage_total = Column(DECIMAL(4,1), default=0)
    contact_stage_total = Column(DECIMAL(4,1), default=0)
    presentation_stage_total = Column(DECIMAL(4,1), default=0)
    objection_stage_total = Column(DECIMAL(4,1), default=0)
    closing_stage_total = Column(DECIMAL(4,1), default=0)
    total_score = Column(DECIMAL(5,1), default=0)
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    call_record = relationship("CallRecord", back_populates="legacy_quality_scores")


class ProcessedFile(Base):
    """Track processed files to avoid re-analysis on restart."""
    __tablename__ = 'processed_files'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String(255), nullable=False, unique=True)  # Google Drive file ID
    file_name = Column(String(500), nullable=False)
    file_modified_time = Column(TIMESTAMP, nullable=False)  # From Google Drive
    status = Column(String(20), default='discovered')  # discovered, processing, completed, failed
    error_message = Column(Text)  # Store error if processing failed
    processed_at = Column(TIMESTAMP)  # When analysis was completed
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    __table_args__ = (
        CheckConstraint("status IN ('discovered', 'processing', 'completed', 'failed')", name='check_processed_file_status'),
        Index('idx_processed_files_file_id', 'file_id'),
        Index('idx_processed_files_status', 'status'),
        Index('idx_processed_files_modified_time', 'file_modified_time'),
    )


# Database session factory
def create_database_engine(database_url: str):
    """Create database engine with proper configuration."""
    engine = create_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
        pool_size=10,
        max_overflow=20,
        pool_recycle=300,
        pool_pre_ping=True
    )
    return engine


def create_session_factory(engine):
    """Create session factory for database operations."""
    Session = sessionmaker(bind=engine)
    return Session


def create_tables(engine):
    """Create all database tables."""
    Base.metadata.create_all(engine)


def drop_tables(engine):
    """Drop all database tables (use with caution!)."""
    Base.metadata.drop_all(engine)