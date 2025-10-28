"""
Database service for VoiceAI Call Analysis System.
Handles all database operations for storing call analysis data.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from loguru import logger

from .database_models import (
    Manager, CallRecord, ChecklistAnalysis, AIAnalysis, LegacyQualityScore,
    create_database_engine, create_session_factory, create_tables
)
from .models import ProcessingResult, AudioFile, ChecklistAnalysisResult, CallAnalysisResult
from .config import config


class DatabaseService:
    """Service for handling database operations."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database service with connection."""
        self.database_url = database_url or config.database_url
        self.engine = create_database_engine(self.database_url)
        self.Session = create_session_factory(self.engine)
        
        # Ensure tables exist
        create_tables(self.engine)
        logger.info("Database service initialized successfully")
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.Session()
    
    def get_or_create_manager(self, manager_name: str, email: Optional[str] = None, 
                             department: Optional[str] = None) -> Optional[Manager]:
        """Get existing manager or create new one."""
        session = self.get_session()
        try:
            # Try to find existing manager
            manager = session.query(Manager).filter(Manager.name == manager_name).first()
            
            if not manager:
                # Create new manager
                manager = Manager(
                    name=manager_name,
                    email=email,
                    department=department or "Sales",
                    status='active'
                )
                session.add(manager)
                session.commit()
                logger.info(f"Created new manager: {manager_name}")
            
            return manager
            
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Error creating manager {manager_name}: {e}")
            # Try to get existing manager again
            return session.query(Manager).filter(Manager.name == manager_name).first()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error in get_or_create_manager: {e}")
            return None
        finally:
            session.close()
    
    def create_call_record(self, processing_result: ProcessingResult, manager_name: str) -> Optional[CallRecord]:
        """Create a new call record from processing result."""
        session = self.get_session()
        try:
            # Get or create manager in this session
            manager = session.query(Manager).filter(Manager.name == manager_name).first()
            if not manager:
                # Create new manager in this session
                manager = Manager(
                    name=manager_name,
                    email=None,
                    department="Sales",
                    status='active'
                )
                session.add(manager)
                session.commit()
                session.refresh(manager)
                logger.info(f"Created new manager: {manager_name}")
            
            if not manager:
                logger.error(f"Could not get/create manager: {manager_name}")
                return None
            
            # Create call record
            call_record = CallRecord(
                file_id=processing_result.audio_file.id,
                file_name=processing_result.audio_file.name,
                manager_id=manager.id,
                call_type=processing_result.quality_scores.call_type if processing_result.quality_scores else "Исходящий",
                call_date=processing_result.audio_file.modified_time,
                file_size=processing_result.audio_file.size,
                mime_type=processing_result.audio_file.mime_type,
                transcription_text=processing_result.transcription.text,
                tagged_dialogue=processing_result.tagged_dialogue.content,
                processing_status='completed'
            )
            
            session.add(call_record)
            session.commit()
            session.refresh(call_record)
            
            logger.info(f"Created call record for file: {processing_result.audio_file.name}")
            return call_record
            
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Call record already exists for file {processing_result.audio_file.id}: {e}")
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating call record: {e}")
            return None
        finally:
            session.close()
    
    def save_checklist_analysis(self, call_record: CallRecord, 
                               checklist_result: ChecklistAnalysisResult) -> Optional[ChecklistAnalysis]:
        """Save checklist analysis results to database."""
        session = self.get_session()
        try:
            # Map checklist result fields to database fields
            field_mapping = {
                # Stage GREETING
                "Time before connecting to manager": "greeting_time_before_manager",
                "Corporate greeting": "greeting_corporate_greeting", 
                "Tone friendly and cheerful, smile in voice": "greeting_tone_friendly",
                "Does not rush or swallow words": "greeting_no_rush_words",
                "States the purpose of the call (info reason)": "greeting_states_purpose",
                "Does not use phrase 'is it convenient to talk'": "greeting_no_convenient_phrase",
                "Does not use phrase 'how can I address you'": "greeting_no_address_phrase",
                
                # Stage CONTACT ESTABLISHMENT
                "Addresses by name at least twice": "contact_addresses_by_name",
                "Does not interrupt, listens fully": "contact_no_interrupt",
                "Speaks in simple clear language": "contact_simple_language",
                "Avoids dry formal tone": "contact_avoids_formal_tone",
                "Communicates as equal": "contact_communicates_equal",
                "Uses small talk (weather, events, hobbies, travel, etc.)": "contact_uses_small_talk",
                "Gives compliment or praise": "contact_gives_compliment",
                "Uses humor (joke, anecdote)": "contact_uses_humor",
                
                # Stage PROGRAMMING
                "Uses programming at start to control conversation": "programming_uses_at_start",
                "Leads conversation throughout": "programming_leads_conversation",
                
                # Stage NEED IDENTIFICATION
                "Asks required questions": "need_asks_required_questions",
                "Finds out company's business area": "need_finds_business_area",
                
                # Stage PRESENTATION
                "Presents company": "presentation_presents_company",
                "Presents 2–3 services with benefits": "presentation_services_with_benefits",
                "Mentions positive cases or reviews": "presentation_mentions_cases",
                "Offers to send proposal or test period": "presentation_offers_proposal",
                "Manager knows product, no mistakes": "presentation_knows_product",
                
                # Stage HANDLING OBJECTIONS
                "Handles all objections fully": "objections_handles_fully",
                "Agrees and empathizes during objection": "objections_agrees_empathizes",
                "Arguments match objection": "objections_arguments_match",
                "Does not argue or violate boundaries": "objections_no_argue",
                "Offers to send proposal after objection": "objections_offers_proposal",
                
                # Stage CLOSING
                "Asks if questions remain": "closing_asks_questions_remain",
                "Clarifies where to send proposal": "closing_clarifies_proposal_send",
                "Asks by what date service needed": "closing_asks_service_date",
                "Summarizes conversation": "closing_summarizes_conversation",
                "States next steps and deadlines": "closing_states_next_steps",
                "Leaves contacts and thanks client": "closing_leaves_contacts",
            }
            
            # Create checklist analysis record
            analysis = ChecklistAnalysis(call_record_id=call_record.id)
            
            # Set scores from all stages
            for stage_name, stage_data in [
                ("Stage GREETING", checklist_result.stage_greeting),
                ("Stage CONTACT ESTABLISHMENT", checklist_result.stage_contact_establishment),
                ("Stage PROGRAMMING", checklist_result.stage_programming),
                ("Stage NEED IDENTIFICATION", checklist_result.stage_need_identification),
                ("Stage PRESENTATION", checklist_result.stage_presentation),
                ("Stage HANDLING OBJECTIONS", checklist_result.stage_handling_objections),
                ("Stage CLOSING", checklist_result.stage_closing),
            ]:
                if isinstance(stage_data, dict):
                    for field_name, score in stage_data.items():
                        if field_name != "Total" and field_name in field_mapping:
                            db_field = field_mapping[field_name]
                            if hasattr(analysis, db_field):
                                setattr(analysis, db_field, float(score) if score is not None else 0)
            
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            
            logger.info(f"Saved checklist analysis for call record {call_record.id}")
            return analysis
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving checklist analysis: {e}")
            return None
        finally:
            session.close()
    
    def save_ai_analysis(self, call_record: CallRecord, 
                        ai_result: CallAnalysisResult) -> Optional[AIAnalysis]:
        """Save AI analysis results to database."""
        session = self.get_session()
        try:
            analysis = AIAnalysis(
                call_record_id=call_record.id,
                summary=ai_result.summary,
                client_talks_most=ai_result.client_talks_most,
                client_name=ai_result.client_name,
                style_adaptation=ai_result.style_adaptation,
                target_client=ai_result.target_client,
                client_needs=ai_result.client_needs,
                manager_responsible=ai_result.manager_responsible,
                
                # Evaluation scores
                contact_establishment_value=ai_result.contact_establishment.value,
                contact_establishment_explanation=ai_result.contact_establishment.explanation,
                
                qualification_value=ai_result.qualification.value,
                qualification_explanation=ai_result.qualification.explanation,
                
                needs_identification_value=ai_result.needs_identification.value,
                needs_identification_explanation=ai_result.needs_identification.explanation,
                
                product_presentation_value=ai_result.product_presentation.value,
                product_presentation_explanation=ai_result.product_presentation.explanation,
                
                objection_handling_value=ai_result.objection_handling.value,
                objection_handling_explanation=ai_result.objection_handling.explanation,
                
                closing_value=ai_result.closing.value,
                closing_explanation=ai_result.closing.explanation,
                
                sale_probability_value=ai_result.sale_probability.value,
                sale_probability_explanation=ai_result.sale_probability.explanation,
                
                # Additional fields
                hidden_objections=ai_result.hidden_objections,
                next_step=ai_result.next_step
            )
            
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            
            logger.info(f"Saved AI analysis for call record {call_record.id}")
            return analysis
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving AI analysis: {e}")
            return None
        finally:
            session.close()
    
    def save_processing_result(self, processing_result: ProcessingResult, 
                              manager_name: str) -> bool:
        """Save complete processing result to database."""
        try:
            # Create call record
            call_record = self.create_call_record(processing_result, manager_name)
            if not call_record:
                logger.error("Failed to create call record")
                return False
            
            # Save checklist analysis if available
            if processing_result.checklist_analysis:
                checklist_analysis = self.save_checklist_analysis(call_record, processing_result.checklist_analysis)
                if not checklist_analysis:
                    logger.warning("Failed to save checklist analysis")
            
            # Save AI analysis if available
            if processing_result.detailed_analysis:
                ai_analysis = self.save_ai_analysis(call_record, processing_result.detailed_analysis)
                if not ai_analysis:
                    logger.warning("Failed to save AI analysis")
            
            logger.info(f"Successfully saved processing result for {processing_result.audio_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving processing result: {e}")
            return False
    
    def get_manager_statistics(self, manager_name: str, days: int = 30) -> Dict[str, Any]:
        """Get performance statistics for a manager."""
        session = self.get_session()
        try:
            manager = session.query(Manager).filter(Manager.name == manager_name).first()
            if not manager:
                return {}
            
            # Get calls in specified period
            from sqlalchemy import and_, func
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            calls = session.query(CallRecord).filter(
                and_(
                    CallRecord.manager_id == manager.id,
                    CallRecord.call_date >= cutoff_date
                )
            ).all()
            
            # Calculate statistics
            total_calls = len(calls)
            inbound_calls = len([c for c in calls if c.call_type == 'Входящий'])
            outbound_calls = len([c for c in calls if c.call_type == 'Исходящий'])
            
            # Get average scores
            checklist_scores = []
            ai_scores = []
            
            for call in calls:
                if call.checklist_analysis:
                    checklist_scores.append(call.checklist_analysis[0].overall_total)
                if call.ai_analysis:
                    ai_scores.append(call.ai_analysis[0].average_score)
            
            return {
                "manager_name": manager_name,
                "period_days": days,
                "total_calls": total_calls,
                "inbound_calls": inbound_calls,
                "outbound_calls": outbound_calls,
                "avg_checklist_score": sum(checklist_scores) / len(checklist_scores) if checklist_scores else 0,
                "avg_ai_score": sum(ai_scores) / len(ai_scores) if ai_scores else 0,
                "last_call_date": max([c.call_date for c in calls]) if calls else None
            }
            
        except Exception as e:
            logger.error(f"Error getting manager statistics: {e}")
            return {}
        finally:
            session.close()
    
    def get_all_managers(self) -> List[Manager]:
        """Get list of all active managers."""
        session = self.get_session()
        try:
            return session.query(Manager).filter(Manager.status == 'active').all()
        except Exception as e:
            logger.error(f"Error getting managers: {e}")
            return []
        finally:
            session.close()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            session = self.get_session()
            
            # Test connection and basic query
            manager_count = session.query(Manager).count()
            call_count = session.query(CallRecord).count()
            
            session.close()
            
            return {
                "status": "healthy",
                "managers_count": manager_count,
                "calls_count": call_count,
                "database_url": self.database_url.split('@')[1] if '@' in self.database_url else "local"
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }